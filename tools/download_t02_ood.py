"""Download a fixed Wikimedia Commons CC0 photo selection for local OOD testing."""
import concurrent.futures
import hashlib
import html
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

import pandas as pd
from PIL import Image

SELECTION = [
 ('Busy crossroads at daytime in Budapest (Unsplash).jpg','day'),
 ('Downtown daytime traffic with taxis (Unsplash).jpg','day'),
 ('Bleak city street (Unsplash).jpg','day'),
 ('Bike on rainy street (Unsplash).jpg','day'),
 ('Christmas Day on Stone Street.jpg','day'),
 ('Nighttime Traffic (Unsplash).jpg','night'),
 ('Nighttime Traffic 1 (Unsplash).jpg','night'),
 ('Colorful urban traffic at night (Unsplash).jpg','night'),
 ('Street at night, black and white.jpg','night'),
 ('Traffic at night (Unsplash).jpg','night'),
]
ROOT=Path('data/ood/t02_web_source')


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'EducationalT02Lab/1.0 (local classroom image quality study)'})
    with urllib.request.urlopen(request,timeout=45) as r: return r.read()


def download(entry):
    index,(title,light)=entry
    query=urllib.parse.urlencode(dict(action='query',format='json',titles='File:'+title,
                                     prop='imageinfo',iiprop='url|extmetadata',iiurlwidth=1024))
    payload=json.loads(fetch('https://commons.wikimedia.org/w/api.php?'+query))
    page=next(iter(payload['query']['pages'].values()))
    info=page['imageinfo'][0];meta=info['extmetadata']
    license=meta.get('LicenseShortName',{}).get('value','')
    if license not in {'CC0','CC0 1.0','Public domain','PDM'}:
        raise ValueError(f'Unexpected license for {title}: {license}')
    url=info.get('thumburl',info['url'])
    blob=fetch(url)
    image=Image.open(io.BytesIO(blob)).convert('RGB')
    image.thumbnail((1024,1024))
    path=ROOT/f'ood_{index:02d}.jpg'
    image.save(path,quality=95)
    (ROOT/f'ood_{index:02d}.metadata.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    def clean(key): return html.unescape(re.sub('<[^>]+>','',meta.get(key,{}).get('value','')))
    return dict(image_id=f'ood_{index:02d}',filename=path.name,title=title,light=light,
                source_page=info['descriptionurl'],download_url=url,original_url=info['url'],
                author=clean('Artist'),license=license,license_url=clean('LicenseUrl'),
                retrieved_date='2026-11-14',download_sha256=hashlib.sha256(blob).hexdigest(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                preprocessing='Wikimedia preview; max side 1024; RGB JPEG quality95; no injected defects')


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(download,enumerate(SELECTION,1)))
    pd.DataFrame(rows).to_csv(ROOT/'sources.csv',index=False)
    pd.DataFrame(rows).to_csv('reports/t02_ood_sources.csv',index=False)
    print(f'Downloaded {len(rows)} photos to {ROOT}')
    print(pd.DataFrame(rows)[['image_id','license','light','title']].to_string(index=False))


if __name__=='__main__': main()
