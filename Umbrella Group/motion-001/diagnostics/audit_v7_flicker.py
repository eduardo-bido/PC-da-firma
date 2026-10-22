"""Trace umbrella flicker through original PNGs, source MP4 and final MP4."""
from pathlib import Path
import json
import subprocess
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parents[1]
FFMPEG='C:/Program Files/ShareX/ffmpeg.exe'
def decode(path):
    r=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-vf','scale=270:480',
        '-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True)
    return np.frombuffer(r.stdout,dtype=np.uint8).reshape(-1,480,270,3)
def roi(arr):return arr[:,235:365,30:240].astype(float)
if __name__=='__main__':
    base=decode(HERE/'hyperframes-v7/assets/continuous-take.mp4')
    final=decode(HERE/'v7/motion-001-v7-1080x1920.mp4')
    original=np.stack([np.asarray(Image.open(HERE/f'v7-frames-1080/frame-{i:04}.png').resize((270,480)))
        for i in range(288,481)])
    a,b,c=roi(base[288:]),roi(final[288:]),roi(original)
    result={}
    for name,data in [('original_png',c),('source_mp4',a),('final_mp4',b)]:
        diff=np.abs(np.diff(data,axis=0)).mean(axis=(1,2,3))
        indexes=np.argsort(diff)[-12:][::-1]
        result[name]={'mean_delta':float(diff.mean()),'max_delta':float(diff.max()),
            'largest':[{'frame':int(i+289),'time':round((i+289)/24,4),'delta':round(float(diff[i]),5)} for i in indexes]}
    result['final_vs_source_same_frame_mae']=float(np.abs(b-a).mean())
    result['source_vs_png_mae']=float(np.abs(a-c).mean())
    # Match final frames to nearby source frames, catching duplicate/out-of-order capture.
    matches=[]
    for i in range(len(a)):
        indices=list(range(max(0,i-3),min(len(a),i+4)))
        scores=[np.abs(b[i]-a[j]).mean() for j in indices]
        j=indices[int(np.argmin(scores))]
        if j!=i:matches.append({'frame':i+288,'nearest_source_frame':j+288,'mae':float(min(scores))})
    result['capture_nearest_frame_mismatches']=matches
    (HERE/'diagnostics/v7-flicker-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
