"""Regression: original one-frame flashes must disappear from the actual export."""
from pathlib import Path
import json
import numpy as np
from audit_v7_flicker import decode,roi

HERE=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    old=roi(decode(HERE/'v7/motion-001-v7-1080x1920.mp4')[288:])
    new=roi(decode(HERE/'v7-1/motion-001-v7-1-1080x1920.mp4')[288:])
    a=np.abs(np.diff(old,axis=0)).mean(axis=(1,2,3))
    b=np.abs(np.diff(new,axis=0)).mean(axis=(1,2,3))
    assert len(new)==193,'Export must keep all final frames'
    assert a.max()>10,'Original visible failure must be reproduced'
    assert b.max()<1.5,f'Unexpected flash remains: ROI delta {b.max():.4f}'
    checks=[]
    for frame in (319,365):
        j=frame-289
        checks.append({'frame':frame,'time':frame/24,'before':float(max(a[j:j+2])),
                       'after':float(max(b[j:j+2]))})
    report={'status':'passed','scope':'Umbrella ROI for every consecutive exported frame from 12 s to end',
        'threshold':1.5,'original_max_delta':float(a.max()),'revised_max_delta':float(b.max()),
        'original_mean_delta':float(a.mean()),'revised_mean_delta':float(b.mean()),'repairs':checks,
        'measurement':'Mean absolute RGB difference on 270x480 decoded video, umbrella region x30:240 y235:365. Units 0..255.',
        'limits':'Checks the reported lighting flashes. Does not certify all aesthetics, motion or audio.'}
    (HERE/'v7-1/flicker-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
