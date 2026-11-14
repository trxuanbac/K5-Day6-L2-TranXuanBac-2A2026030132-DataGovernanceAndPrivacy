"""Descriptive run comparison. Never fabricate official GT-based metrics."""
from pathlib import Path
import json

import pandas as pd
from PIL import Image, ImageDraw

from src.common.io import write_json


def main():
    rows, runs = [], {}
    for name in ['baseline', 'poc']:
        folder = Path('out/t02') / name
        info = json.loads((folder/'run_info.json').read_text())
        pred = pd.read_csv(folder/'ranked_review.csv')
        raw = pd.read_csv(folder/'predictions_raw.csv')
        runs[name] = dict(n_items=len(pred), n_reviewed=info['stats'].get('n_reviewed',0),
                          action_counts=pred.pred_action.value_counts().to_dict(),
                          runtime_seconds=info['runtime_seconds'],
                          runtime_per_100_items_s=100*info['runtime_seconds']/len(pred),
                          model_action_counts=raw.pred_action.value_counts().to_dict())
        for split, group in pred.groupby('split'):
            for light, sub in group.groupby('light'):
                rows.append(dict(run=name, split=split, light=light, n=len(sub),
                                 keep=int((sub.pred_action=='KEEP').sum()),
                                 recapture=int((sub.pred_action=='RECAPTURE').sum()),
                                 review=int((sub.pred_action=='REVIEW').sum())))
    write_json('reports/t02_run_summary.json', dict(official_metrics_status='PENDING_INSTRUCTOR_GT',
               warning='Descriptive counts only, not recall, precision or correctness.',runs=runs))
    pd.DataFrame(rows).to_csv('reports/t02_slices.csv',index=False)
    b,p = runs['baseline'],runs['poc']
    lines=['# Baseline vs PoC — descriptive evidence', '',
           'Official Defect Recall@20 and Precision@20: pending instructor GT. Counts below do not measure correctness.', '',
           '| Item | Baseline | PoC |','|---|---:|---:|']
    for key in ['n_items','n_reviewed','runtime_per_100_items_s']:
        lines.append(f'| {key} | {b[key]} | {p[key]} |')
    for action in ['KEEP','RECAPTURE','REVIEW']:
        lines.append(f"| {action} after review | {b['action_counts'].get(action,0)} | {p['action_counts'].get(action,0)} |")
    Path('reports/table1_baseline_vs_poc.md').write_text('\n'.join(lines)+'\n')
    # Small visual evidence for the demo; original fixture images are not modified.
    ids=['img_09_2','img_04_3','img_12_0','img_15_3']
    metadata=pd.read_csv('fixtures/t02_raw_qc/images.csv').set_index('image_id')
    reviewed=pd.read_csv('reports/reviewed_images.csv').set_index('item_id').fillna('')
    sheet=Image.new('RGB',(680,480),'white');draw=ImageDraw.Draw(sheet)
    for i,iid in enumerate(ids):
        x=(i%2)*340;y=(i//2)*240
        with Image.open(Path('fixtures/t02_raw_qc')/metadata.loc[iid,'path']) as image:
            sheet.paste(image.convert('RGB').resize((320,180)),(x+10,y+10))
        decision=reviewed.loc[iid,'override_value'] or reviewed.loc[iid,'reviewer_decision']
        draw.text((x+10,y+195),f'{iid} | {decision}',fill='black')
    Path('demo').mkdir(exist_ok=True)
    sheet.save('demo/t02_examples.png')
    print('Generated reports/t02_run_summary.json, t02_slices.csv, comparison and demo/t02_examples.png')


if __name__=='__main__':
    main()
