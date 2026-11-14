"""T02 CPU quality triage, dev-only calibration and auditable image review."""
from pathlib import Path

import numpy as np
import pandas as pd

from .common.contact_sheet import render_contact_sheet
from .common.decision import Decision, write_decision
from .common.image_ops import brightness_stats, laplacian_variance, load_rgb, to_gray
from .common.io import write_json, sha256_file, read_json
from .common.review import load_review_decisions, make_review_queue, write_review_queue


DEFAULTS = dict(blur_quantile=0.25, min_group_size=6, dark_mean=35.0,
                dark_fraction=0.75, glare_fraction=0.20, compression_ratio=1.8,
                defect_threshold=0.5)


def metadata(ctx):
    df = pd.read_csv(ctx.input_dir / 'images.csv', dtype=str)
    required = ['image_id', 'path', 'camera_id', 'light', 'split']
    if not set(required) <= set(df):
        raise ValueError('images.csv missing required columns')
    if df.empty or df[required].isna().any().any() or df[required].apply(lambda c: c.str.strip().eq('')).any().any():
        raise ValueError('images.csv has empty required values')
    if df.image_id.duplicated().any():
        raise ValueError('Duplicate image_id')
    root = ctx.input_dir.resolve()
    for path in df.path:
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root) or 'gt' in resolved.relative_to(root).parts:
            raise ValueError(f'Image path outside permitted input: {path}')
        if not resolved.is_file():
            raise FileNotFoundError(f'Missing image: {path}')
    return df


def blockiness(gray):
    """Ratio of adjacent differences at JPEG 8-pixel boundaries to other edges."""
    values = []
    for axis in (0, 1):
        diff = np.abs(np.diff(gray, axis=axis))
        positions = np.arange(1, gray.shape[axis])
        boundary = positions % 8 == 0
        if boundary.any() and (~boundary).any():
            means = diff.mean(axis=1-axis)
            values.append(float(means[boundary].mean() / (means[~boundary].mean() + 1.0)))
    return max(values, default=0.0)


def extract_features(ctx, images):
    rows = []
    for row in images.itertuples(index=False):
        image = load_rgb(ctx.input_dir / row.path)
        gray = to_gray(image)
        # Saturation in tiles detects local glare hidden by global brightness.
        tiles = [tile for strip in np.array_split(gray, 4, axis=0)
                 for tile in np.array_split(strip, 4, axis=1) if tile.size]
        rows.append(dict(sharpness=laplacian_variance(image), **brightness_stats(image),
                         local_saturation=max(float((tile > 245).mean()) for tile in tiles),
                         blockiness=blockiness(gray)))
    return pd.concat([images.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def calibrate(features, params):
    dev = features[features.split == 'dev']
    if dev.empty:
        raise ValueError('Dev split required for calibration; eval is never used to fit thresholds')
    quantile = float(params['blur_quantile'])
    if not 0 < quantile < 1:
        raise ValueError('blur_quantile must be between 0 and 1')
    global_threshold = max(float(dev.sharpness.quantile(quantile)), 1e-6)
    groups = {}
    for keys, sub in dev.groupby(['camera_id', 'light'], sort=True):
        if len(sub) >= int(params['min_group_size']):
            groups['|'.join(keys)] = max(float(sub.sharpness.quantile(quantile)), 1e-6)
    return dict(fit_split='dev', n_fit=len(dev), global_blur_threshold=global_threshold,
                group_blur_thresholds=groups, params=params)


def score_features(features, calibration, baseline=False):
    df = features.copy()
    params = calibration['params']
    global_threshold = calibration['global_blur_threshold']
    thresholds = np.full(len(df), global_threshold)
    if not baseline:
        thresholds = np.array([calibration['group_blur_thresholds'].get(f'{r.camera_id}|{r.light}', global_threshold)
                               for r in df.itertuples()])
    df['blur_score'] = np.clip(1.0 - df.sharpness.to_numpy() / (2.0 * thresholds), 0, 1)
    if baseline:
        df['score'] = 1.0 / (df.sharpness + 1e-6)
        df['pred_defect_type'] = np.where(df.sharpness < global_threshold, 'blur', 'none')
        df['pred_action'] = np.where(df.sharpness < global_threshold, 'RECAPTURE', 'KEEP')
        df['reason'] = 'global_laplacian_threshold'
    else:
        df['dark_score'] = np.maximum(
            np.clip(1.0 - df['mean'] / (2 * params['dark_mean']), 0, 1),
            np.clip((df.frac_dark - params['dark_fraction']) / (1 - params['dark_fraction']), 0, 1))
        df['glare_score'] = np.clip(df.local_saturation / params['glare_fraction'], 0, 1)
        df['compression_score'] = np.clip((df.blockiness - 1.0) / params['compression_ratio'], 0, 1)
        scores = df[['blur_score', 'dark_score', 'glare_score', 'compression_score']].to_numpy()
        df['score'] = scores.max(axis=1)
        kinds = np.array(['blur', 'dark', 'glare', 'compression'])[scores.argmax(axis=1)]
        defective = df.score >= params['defect_threshold']
        df['pred_defect_type'] = np.where(defective, kinds, 'none')
        df['pred_action'] = np.where(defective, 'RECAPTURE', 'KEEP')
        df['reason'] = [f'{kind}; sharpness={s:.2f}; brightness={b:.1f}; local_sat={g:.3f}'
                        for kind, s, b, g in zip(df.pred_defect_type, df.sharpness, df['mean'], df.local_saturation)]
    df['model_action'] = df.pred_action
    df['reviewer'] = ''
    df['review_status'] = 'unreviewed'
    df['review_note'] = ''
    return df


def process(ctx, images, baseline=False):
    params = {key: float(ctx.param(key, value)) for key, value in DEFAULTS.items()}
    if any(not np.isfinite(v) for v in params.values()):
        raise ValueError('Quality parameters must be finite')
    if not 0 < params['dark_fraction'] < 1 or not 0 < params['defect_threshold'] < 1:
        raise ValueError('dark_fraction and defect_threshold must be between 0 and 1')
    if any(params[k] <= 0 for k in ['dark_mean', 'glare_fraction', 'compression_ratio', 'min_group_size']):
        raise ValueError('Feature thresholds must be positive')
    features = extract_features(ctx, images)
    features.to_csv(ctx.out('features.csv'), index=False)
    frozen = ctx.param('calibration_file')
    if frozen:
        calibration = read_json(frozen)
        if calibration.get('fit_split') != 'dev' or not isinstance(calibration.get('group_blur_thresholds'), dict):
            raise ValueError('Invalid frozen calibration schema')
        saved_params = calibration.get('params', {})
        if set(DEFAULTS) - saved_params.keys() or any(not np.isfinite(float(v)) for v in saved_params.values()):
            raise ValueError('Invalid frozen calibration parameters')
        if not 0 < saved_params['dark_fraction'] < 1 or not 0 < saved_params['defect_threshold'] < 1:
            raise ValueError('Invalid frozen calibration fractions')
        if any(saved_params[k] <= 0 for k in ['dark_mean', 'glare_fraction', 'compression_ratio', 'min_group_size']):
            raise ValueError('Invalid frozen calibration thresholds')
        thresholds = [calibration.get('global_blur_threshold', 0), *calibration['group_blur_thresholds'].values()]
        if any(not np.isfinite(float(v)) or float(v) <= 0 for v in thresholds):
            raise ValueError('Invalid frozen blur thresholds')
        ctx.audit.log(actor='pipeline', action='frozen_calibration_loaded', item_id='t02',
                      after={'path': str(frozen), 'sha256': sha256_file(frozen)})
    else:
        calibration = calibrate(features, params)
    write_json(ctx.out('calibration.json'), calibration)
    return score_features(features, calibration, baseline)


def rank(ctx, scored):
    budget = int(ctx.param('budget', 20))
    if budget <= 0:
        raise ValueError('budget must be positive')
    queue = make_review_queue(scored, 'image_id', 'score', budget, reason_col='reason',
                              action_col='pred_action', slice_col='light', evidence_col='path')
    write_review_queue(queue, ctx.out('review_queue.csv'))
    render_contact_sheet(queue, ctx.out('contact_sheet.html'), image_root=ctx.input_dir,
                         title=f'T02 - {ctx.run_name} review')
    return queue


def review(ctx, scored, queue):
    """Review changes actions only; ranking scores remain frozen for fair evaluation."""
    final = scored.copy()
    paths = [ctx.output_dir / 'review_queue_reviewed.csv']
    imported = ctx.param('review_import')
    if imported and Path(imported) != paths[0]:
        expected = ctx.param('review_manifest_sha256')
        manifest = ctx.input_dir / 'manifest.csv'
        if expected and manifest.exists() and sha256_file(manifest) == expected:
            paths.insert(0, Path(imported))
        else:
            ctx.audit.log(actor='pipeline', action='review_import_skipped', item_id='t02',
                          reason='Review evidence belongs to a different or unverified input manifest')
    known = set(final.image_id)
    total_ids = set()
    for path in paths:
        if not path.exists():
            if str(path) == str(imported):
                raise FileNotFoundError(f'Review import not found: {path}')
            continue
        reviewed = load_review_decisions(path)
        if reviewed.item_id.duplicated().any():
            raise ValueError('Duplicate reviewed image_id')
        if not set(reviewed.item_id) <= known:
            raise ValueError('Review refers to unknown image_id')
        if len(reviewed) > int(ctx.param('budget', 20)):
            raise ValueError('Reviewed file exceeds budget')
        for r in reviewed.itertuples(index=False):
            mask = final.image_id == r.item_id
            old = final.loc[mask, 'pred_action'].iloc[0]
            action = old
            if r.reviewer_decision in ('edit', 'reject'):
                action = r.override_value.strip().upper()
                if action not in {'KEEP', 'RECAPTURE'} or not r.review_note.strip():
                    raise ValueError('Edit/reject requires KEEP or RECAPTURE and a review note')
            elif r.reviewer_decision == 'escalate':
                action = 'REVIEW'
            if r.reviewer_decision == 'skip':
                status = 'skipped'
            else:
                status = 'escalated' if r.reviewer_decision == 'escalate' else 'reviewed'
                total_ids.add(r.item_id)
            final.loc[mask, ['pred_action', 'reviewer', 'review_status', 'review_note']] = [action, r.reviewer, status, r.review_note]
            ctx.audit.log(actor=r.reviewer, action='review:' + r.reviewer_decision, item_id=r.item_id,
                          before=old, after=action, reason=r.review_note, source=str(path))
    if len(total_ids) > int(ctx.param('budget', 20)):
        raise ValueError('Combined reviewed images exceed budget')
    ctx.stats['n_reviewed'] = len(total_ids)
    return final


def decide(ctx, final):
    if (final.pred_action == 'REVIEW').any():
        status, code = 'HOLD', 'REVIEW_ESCALATION_PENDING'
    elif (final.pred_action == 'RECAPTURE').any():
        status, code = 'REWORK', 'RECAPTURE_REQUIRED'
    else:
        # Unreviewed predictions do not constitute human release approval.
        status, code = 'HOLD', 'OWNER_RELEASE_APPROVAL_REQUIRED'
    return Decision(status=status, reason_code=code,
                    reason=f"KEEP={(final.pred_action == 'KEEP').sum()}, RECAPTURE={(final.pred_action == 'RECAPTURE').sum()}, REVIEW={(final.pred_action == 'REVIEW').sum()}",
                    owner=ctx.config['owner'], scope='t02',
                    evidence=[str(ctx.out('ranked_review.csv')), str(ctx.out('audit_log.jsonl'))])


def finish(ctx, scored, queue):
    scored.sort_values('score', ascending=False, kind='mergesort').to_csv(ctx.out('predictions_raw.csv'), index=False)
    final = review(ctx, scored, queue).sort_values('score', ascending=False, kind='mergesort')
    final.to_csv(ctx.out('ranked_review.csv'), index=False)
    final[final.review_status != 'unreviewed'].to_csv(ctx.out('review_results.csv'), index=False)
    ctx.stats.update(n_items=len(final), action_counts=final.pred_action.value_counts().to_dict())
    write_decision(decide(ctx, final), ctx.out('decision.json'), ctx.out('decision_log.csv'))
