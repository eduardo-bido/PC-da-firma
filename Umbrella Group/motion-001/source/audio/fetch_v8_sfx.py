"""Fetch public HQ previews only after verifying CC0 on each author page."""
from pathlib import Path
import urllib.request
import re
import json
import hashlib

HERE=Path(__file__).resolve().parent
SOURCES=[('KVV_Audio',729226,'cinematic-whoosh'),('Qat',108334,'whoosh-click'),
         ('jackhilton',444771,'placemat-wobble'),('LewisEmmott5',732684,'wooden-object-thuds')]
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(req,timeout=45).read()
if __name__=='__main__':
    records=[]
    for author,id,name in SOURCES:
        page=f'https://freesound.org/people/{author}/sounds/{id}/'
        text=get(page).decode('utf-8')
        if 'creativecommons.org/publicdomain/zero/1.0' not in text:
            raise ValueError(f'CC0 not verified: {page}')
        links=sorted(set(re.findall(r'https://[^\s\"<>]+-hq\.mp3',text)))
        links=[s.replace('\\/','/') for s in links if str(id) in s]
        if len(links)!=1:raise ValueError(f'Expected one public HQ preview: {links}')
        output=HERE/f'{name}-{id}-cc0.mp3'
        output.write_bytes(get(links[0]))
        records.append({'author':author,'id':id,'file':output.name,'source':page,
            'preview':links[0],'license':'CC0 1.0 Universal','license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
            'checked':'2026-10-23','bytes':output.stat().st_size,
            'sha256':hashlib.file_digest(output.open('rb'),'sha256').hexdigest()})
        (HERE/'v8-sfx-manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print(name,'CC0 verified, public preview downloaded.',flush=True)
