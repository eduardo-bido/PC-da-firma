"""Local V8 finishing: preserve approved voice/captions and build revised cinema SFX."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import prepare_v7 as previous

HERE=Path(__file__).resolve().parent
PROJECT=HERE/'hyperframes-v8'
ASSETS=PROJECT/'assets'

def encode_take(frames,ffmpeg,duration):
    # A single physical camera take: no finishing crop, reverse or digital zoom.
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','24',
        '-i',str(frames/'frame-%04d.png'),'-frames:v',str(round(duration*24)),
        '-c:v','libx264','-crf','15','-g','24','-keyint_min','24','-sc_threshold','0',
        '-pix_fmt','yuv420p','-vf',
        'scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
        '-movflags','+faststart',str(ASSETS/'continuous-take.mp4')],check=True)
    shutil.copy2(frames/'render-report.json',ASSETS/'continuous-take.render.json')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--frames',type=Path)
    p.add_argument('--ffmpeg',default='ffmpeg')
    p.add_argument('--reference',type=Path,help='Local authorized slow-motion audio; not distributed in the public repository')
    a=p.parse_args()
    ASSETS.mkdir(parents=True,exist_ok=True)
    (HERE/'v8').mkdir(exist_ok=True)
    for name in ('package.json','package-lock.json'):
        shutil.copy2(HERE/'hyperframes-v7'/name,PROJECT/name)
    for name in ('narration.wav','narration-dry.wav','voice-demo.wav','narration.json','captions.srt','transcription.json'):
        shutil.copy2(HERE/'hyperframes-v7/assets'/name,ASSETS/name)
    meta=json.loads((ASSETS/'narration.json').read_text(encoding='utf-8'))
    meta['version']='v8'
    meta['revision']='Approved V7.1 voice/captions unchanged. Visible initial fall, wall branding, exact user-selected slow-motion reference and recorded Foley.'
    (ASSETS/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    previous.PROJECT=PROJECT
    previous.ASSETS=ASSETS
    previous.build()
    if a.frames:encode_take(a.frames.resolve(),a.ffmpeg,meta['duration'])
    # The rejected quiet filtered-noise sketch is not part of the render path.
    sound_command=[sys.executable,str(HERE/'design_v8_reference.py'),'--ffmpeg',a.ffmpeg]
    if a.reference:sound_command+=['--reference',str(a.reference.resolve())]
    subprocess.run(sound_command,check=True)
    print('V8 composition and revised local sound ready.',flush=True)
