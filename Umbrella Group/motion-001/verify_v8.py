"""Verify V8 hook, protected narration, revised SFX and late-frame stability."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import wave
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
def pcm(path):
    with wave.open(str(path),'rb') as w:
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,w.getnchannels()),w.getframerate()
def decode(path,ffmpeg):
    r=subprocess.run([ffmpeg,'-v','error','-i',str(path),'-vf','scale=270:480',
        '-pix_fmt','rgb24','-f','rawvideo','pipe:1'],check=True,capture_output=True)
    return np.frombuffer(r.stdout,dtype=np.uint8).reshape(-1,480,270,3)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ffmpeg',default='ffmpeg');a=p.parse_args()
    project=HERE/'hyperframes-v8';out=HERE/'v8'
    old=(HERE/'hyperframes-v7/assets/narration.wav').read_bytes()
    new=(project/'assets/narration.wav').read_bytes()
    assert new==old,'Approved narration must not change'
    fx,rate=pcm(project/'assets/foley.wav')
    assert rate==48000 and len(fx)==962000
    assert np.abs(fx.astype(float)).max()<32767,'SFX has no sample headroom'
    sound=json.loads((out/'sound-design.json').read_text())
    events={v['stem'] for v in sound['events']}
    required={'exact_user_slow_motion_reference','recorded_tip_contact','real_umbrella_blauf','bounce_poc_1','bounce_poc_2','rolling_rrruom_1','rolling_rrruom_2'}
    assert required.issubset(events),'Requested cinematic event layers missing'
    assert not np.any(fx[round(4.92*rate):5*rate]),'80ms pre-contact pocket missing'
    layout=json.loads((out/'layout-report.json').read_text())
    descent=(layout['0']['tip_uv'][1]-layout['0.35']['tip_uv'][1])*1920
    assert descent>130,'The first 0.35s fall must be clearly visible'
    assert layout['3.4']['mark_box_uv'][1]>1,'Wall mark must leave the macro frame naturally'
    final=decode(out/'motion-001-v8-1080x1920.mp4',a.ffmpeg)
    assert len(final)==481
    roi=final[288:,235:365,30:240].astype(float)
    deltas=np.abs(np.diff(roi,axis=0)).mean(axis=(1,2,3))
    assert deltas.max()<1.5,f'Lighting flash detected at {12+(np.argmax(deltas)+1)/24:.3f}s: {deltas.max():.3f}'
    # Inspect before/after the previous problem instants in the actual new export.
    crops=[]
    for i in (318,319,320,364,365,366):
        crops.append(Image.fromarray(final[i]).crop((20,210,250,375)).resize((360,260)))
    sheet=Image.new('RGB',(1080,520))
    for i,im in enumerate(crops):sheet.paste(im,((i%3)*360,(i//3)*260))
    sheet.save(out/'late-continuity.png')
    report={'status':'passed','first_035_seconds_tip_descent_pixels_1080':descent,
        'narration_sha256':hashlib.sha256(new).hexdigest(),'narration_bit_identical_to_v7_1':True,
        'sound_revision':sound['version'],'cinematic_event_layers_present':sorted(required),
        'sfx_peak_dbfs':sound['sfx_peak_dbfs'],'pre_contact_silent_pocket_seconds':.08,
        'wall_mark_leaves_macro':True,'late_12s_to_end_max_roi_delta':float(deltas.max()),
        'late_flash_threshold':1.5,'late_frames_tested':len(roi),
        'auditory_review':'Agent did not hear the new sound. No claim of perceptual sound quality from this test.'}
    (out/'creative-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
