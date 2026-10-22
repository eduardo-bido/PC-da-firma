"""Download public Apache-2.0 weights at a fixed revision; no account/API inference."""
from pathlib import Path
import hashlib
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['HF_HUB_DISABLE_XET']='1'

HERE=Path(__file__).resolve().parent
REPO='Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
REVISION='5ecdb67327fd37bb2e042aab12ff7391903235d3'
if __name__=='__main__':
    metadata=json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{REPO}/revision/{REVISION}'))
    def download(item):
        name=item['rfilename']
        if name=='.gitattributes':return
        target=HERE/'model'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():return
        temp=target.with_suffix(target.suffix+'.part')
        url=f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}'
        with urllib.request.urlopen(url,timeout=120) as src,temp.open('wb') as dst:
            while chunk:=src.read(4*1024*1024):dst.write(chunk)
        temp.replace(target)
        print('Downloaded',name,target.stat().st_size,flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(download,metadata['siblings']))
    records=[]
    for p in sorted((HERE/'model').rglob('*')):
        if p.is_file() and '.cache' not in p.parts:
            records.append({'path':p.relative_to(HERE/'model').as_posix(),
                'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
    (HERE/'model-manifest.json').write_text(json.dumps({'repo':REPO,'revision':REVISION,
        'license':'Apache-2.0','files':records},indent=2),encoding='utf-8')
    print('Public model downloaded and hashed.',flush=True)
