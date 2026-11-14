"""Prepare a local 10-image OOD pack, without fitting on its data or publishing it."""
import argparse
from pathlib import Path
import shutil

import pandas as pd
import yaml
from PIL import Image

from src.common.io import load_config
from src.common.manifest import build_manifest, write_manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Folder of authorized images')
    parser.add_argument('--provenance', required=True, help='Actual source / owner description')
    parser.add_argument('--license', required=True, help='Actual permission or license; never inferred')
    parser.add_argument('--output', default='data/ood/t02')
    parser.add_argument('--calibration', default='out/t02/poc/calibration.json')
    args=parser.parse_args()
    source=Path(args.source).resolve(); output=Path(args.output)
    files=sorted(p for p in source.iterdir() if p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'})
    if len(files)<10: parser.error('At least 10 authorized images required')
    if output.exists(): parser.error('Output already exists; choose a new directory')
    calibration=Path(args.calibration)
    if not calibration.is_file(): parser.error('Run the fixture PoC first to save dev calibration')
    for p in files[:10]:
        with Image.open(p) as image: image.verify()
    (output/'images').mkdir(parents=True)
    rows=[]
    for i,p in enumerate(files[:10],1):
        target=output/'images'/f'ood_{i:02d}{p.suffix.lower()}'
        shutil.copy2(p,target)
        rows.append(dict(image_id=f'ood_{i:02d}',path=str(target.relative_to(output)),
                         camera_id='unknown',light='unknown',split='ood'))
    pd.DataFrame(rows).to_csv(output/'images.csv',index=False)
    manifest=build_manifest(output,['images.csv',*[r['path'] for r in rows]],
                            source=args.provenance,license=args.license,split='ood')
    write_manifest(manifest,output/'manifest.csv')
    # Keep a private copy, unaffected by a future fixture run.
    shutil.copy2(calibration,output/'frozen_calibration.json')
    cfg=load_config('configs/lab.yaml');cfg.pop('track_config',None)
    cfg['input']=str(output);cfg['output']='out/t02/ood'
    cfg['params']['calibration_file']=str(output/'frozen_calibration.json')
    cfg['params'].pop('review_import',None);cfg['params'].pop('review_manifest_sha256',None)
    config=output/'lab_ood.yaml';config.write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False))
    print(f'.venv/bin/python -m src.main --config {config} --offline --seed 42')
    print('Review each image manually; do not treat predicted defect labels as ground truth.')


if __name__=='__main__': main()
