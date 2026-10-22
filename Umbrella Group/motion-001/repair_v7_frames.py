"""Repair two anomalous source renders without changing the approved take.

Use the fresh same-scene renders of 319/365; link all other original PNGs.
The original V7 frames and delivered MP4s remain unchanged.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
BAD=(319,365)
def pixels(path):
    return np.asarray(Image.open(path).resize((270,480)),dtype=float)[235:365,30:240]
if __name__=='__main__':
    src=HERE/'v7-frames-1080';fresh=HERE/'v7-flash-repro'
    dest=HERE/'v7-1-frames-1080';dest.mkdir(exist_ok=True)
    report={'version':'v7-1','source':'V7 scene and approved motion unchanged',
        'method':'Two source-frame rerenders in a fresh Blender process. No frame interpolation or frozen image.',
        'diagnosis':'Large one-frame lighting changes exist in original PNGs, source MP4 and final MP4. No transform quaternion sign discontinuity. Fresh renders with same settings reproduce surrounding frames but not the two flashes; exact renderer-internal cache mechanism unproven.',
        'frames':[]}
    for i in BAD:
        before=pixels(src/f'frame-{i-1:04}.png');after=pixels(src/f'frame-{i+1:04}.png')
        old=pixels(src/f'frame-{i:04}.png');new=pixels(fresh/f'frame-{i:04}.png')
        old_delta=max(np.abs(old-before).mean(),np.abs(after-old).mean())
        new_delta=max(np.abs(new-before).mean(),np.abs(after-new).mean())
        if not old_delta>10:raise ValueError('Original failure not reproduced')
        if not new_delta<.5:raise ValueError('Fresh source frame still flashes')
        report['frames'].append({'frame':i,'time':i/24,'original_max_roi_delta':float(old_delta),
            'repaired_max_roi_delta':float(new_delta),
            'sha256':hashlib.file_digest((fresh/f'frame-{i:04}.png').open('rb'),'sha256').hexdigest()})
    for i in range(481):
        p=(fresh if i in BAD else src)/f'frame-{i:04}.png';target=dest/p.name
        if target.exists():continue
        if i in BAD:shutil.copy2(p,target)
        else:
            try:os.link(p,target)
            except OSError:shutil.copy2(p,target)
    out=HERE/'v7-1';out.mkdir(exist_ok=True)
    (out/'repair-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    render=json.loads((src/'render-report.json').read_text(encoding='utf-8'))
    render.update(version='v7-1',repaired_frames=list(BAD),approved_motion_preserved=True)
    (dest/'render-report.json').write_text(json.dumps(render,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
