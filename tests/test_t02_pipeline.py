"""Behavioral tests for dev-only fitting, quality signals and reviewed actions."""
import json

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from src import t02
from src.common.context import RunContext
from src.common.review import AuditLog, make_review_queue


def ctx(tmp_path):
    return RunContext('t02', tmp_path, tmp_path, {'owner':'Tester','params':{'budget':20}},
                      42, np.random.default_rng(42), audit=AuditLog(tmp_path/'audit_log.jsonl'))


def feature_frame():
    return pd.DataFrame(dict(image_id=['a','b','c'],path=['a.jpg','b.jpg','c.jpg'],
        camera_id=['cam']*3,light=['day']*3,split=['dev','dev','eval'],sharpness=[20.,40.,100.],
        mean=[100.,100.,100.],frac_dark=[0.,0.,0.],local_saturation=[0.,0.,0.],blockiness=[1.,1.,1.]))


def test_calibration_does_not_fit_eval():
    f=feature_frame(); first=t02.calibrate(f,t02.DEFAULTS)
    f.loc[f.split=='eval','sharpness']=0.001
    assert first==t02.calibrate(f,t02.DEFAULTS)
    assert first['n_fit']==2


def test_dev_is_required():
    f=feature_frame(); f['split']='eval'
    with pytest.raises(ValueError,match='Dev split'):
        t02.calibrate(f,t02.DEFAULTS)


def test_dark_and_local_glare_are_independent_signals():
    f=feature_frame(); cal=t02.calibrate(f,t02.DEFAULTS)
    f.loc[2,'mean']=0.; f.loc[2,'frac_dark']=1.
    assert t02.score_features(f,cal).loc[2,'pred_defect_type']=='dark'
    f.loc[2,['mean','frac_dark','local_saturation']]=[100.,0.,0.5]
    assert t02.score_features(f,cal).loc[2,'pred_defect_type']=='glare'


def test_review_preserves_ranking_and_logs_override(tmp_path):
    c=ctx(tmp_path); f=feature_frame(); scored=t02.score_features(f,t02.calibrate(f,t02.DEFAULTS))
    q=make_review_queue(scored,'image_id','score',20)
    q.loc[0,['reviewer','reviewer_decision','override_value','review_note']]=['Tester','edit','RECAPTURE','Too blurry']
    q.to_csv(tmp_path/'review_queue_reviewed.csv',index=False)
    final=t02.review(c,scored,q)
    assert final.score.equals(scored.score)
    assert final.loc[final.image_id==q.loc[0,'item_id'],'pred_action'].iloc[0]=='RECAPTURE'
    assert c.audit.read()[0]['actor']=='Tester'


@pytest.mark.parametrize('field,value', [('reviewer',''),('override_value','DELETE'),('review_note',''),('item_id','unknown')])
def test_invalid_review_is_rejected(tmp_path,field,value):
    c=ctx(tmp_path); f=feature_frame(); scored=t02.score_features(f,t02.calibrate(f,t02.DEFAULTS))
    q=make_review_queue(scored,'image_id','score',20)
    q.loc[0,['reviewer','reviewer_decision','override_value','review_note']]=['Tester','edit','KEEP','usable']
    q.loc[0,field]=value
    q.to_csv(tmp_path/'review_queue_reviewed.csv',index=False)
    with pytest.raises(ValueError): t02.review(c,scored,q)


def test_missing_image_and_duplicate_ids(tmp_path):
    c=ctx(tmp_path)
    f=feature_frame()[['image_id','path','camera_id','light','split']]
    f.to_csv(tmp_path/'images.csv',index=False)
    with pytest.raises(FileNotFoundError): t02.metadata(c)
    f.loc[1,'image_id']='a'; f.to_csv(tmp_path/'images.csv',index=False)
    with pytest.raises(ValueError,match='Duplicate'): t02.metadata(c)


def test_broken_image_fails(tmp_path):
    c=ctx(tmp_path); (tmp_path/'a.jpg').write_text('not an image')
    f=feature_frame().head(1)
    with pytest.raises(OSError): t02.extract_features(c,f)


def test_escalation_means_hold(tmp_path):
    c=ctx(tmp_path); f=feature_frame(); scored=t02.score_features(f,t02.calibrate(f,t02.DEFAULTS))
    q=make_review_queue(scored,'image_id','score',20)
    q.loc[0,['reviewer','reviewer_decision','review_note']]=['Tester','escalate','Need original']
    q.to_csv(tmp_path/'review_queue_reviewed.csv',index=False)
    assert t02.decide(c,t02.review(c,scored,q)).status=='HOLD'


def test_end_to_end_offline_and_repeatable(tmp_path):
    from src.main import main
    args=['--track','t02','--output',str(tmp_path),'--offline','--seed','42']
    assert main(args)==0
    before=(tmp_path/'ranked_review.csv').read_bytes()
    assert main(args)==0
    assert (tmp_path/'ranked_review.csv').read_bytes()==before
    assert len(pd.read_csv(tmp_path/'ranked_review.csv'))==96
    assert json.loads((tmp_path/'run_info.json').read_text())['status']==0


def test_old_review_not_applied_to_new_dataset(tmp_path):
    c=ctx(tmp_path)
    c.config['params'].update(review_import=str(tmp_path/'foreign.csv'),review_manifest_sha256='wrong')
    (tmp_path/'manifest.csv').write_text('different manifest')
    f=feature_frame(); scored=t02.score_features(f,t02.calibrate(f,t02.DEFAULTS))
    q=make_review_queue(scored,'image_id','score',20)
    pd.testing.assert_frame_equal(t02.review(c,scored,q),scored)
    assert c.audit.read()[0]['action']=='review_import_skipped'


def test_frozen_calibration_never_refits_ood(tmp_path, monkeypatch):
    c=ctx(tmp_path);f=feature_frame();cal=t02.calibrate(f,t02.DEFAULTS)
    path=tmp_path/'saved.json';path.write_text(json.dumps(cal))
    c.config['params']['calibration_file']=str(path)
    f['split']='ood'
    monkeypatch.setattr(t02,'extract_features',lambda *args:f)
    def forbidden(*args): raise AssertionError('OOD must never fit calibration')
    monkeypatch.setattr(t02,'calibrate',forbidden)
    result=t02.process(c,f)
    pd.testing.assert_frame_equal(result,t02.score_features(f,cal))
    assert json.loads((tmp_path/'calibration.json').read_text())==cal
