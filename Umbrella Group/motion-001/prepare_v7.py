"""Build the editable HyperFrames project from offline narration and a single take."""
from pathlib import Path
import html
import json
import shutil
import subprocess
import argparse

HERE=Path(__file__).resolve().parent
PROJECT=HERE/'hyperframes-v7'
ASSETS=PROJECT/'assets'

def build():
    meta=json.loads((ASSETS/'narration.json').read_text(encoding='utf-8'))
    (ASSETS/'fonts').mkdir(exist_ok=True)
    shutil.copy2(HERE.parent/'public/fonts/Manrope.ttf',ASSETS/'fonts/Manrope.ttf')
    shutil.copy2(PROJECT/'node_modules/gsap/dist/gsap.min.js',ASSETS/'gsap.min.js')
    (PROJECT/'compositions').mkdir(exist_ok=True)
    duration=meta['duration']
    captions=[]
    for cue in meta['cues']:
        if cue['text']=='Umbrella.':continue # The brand title is the caption here.
        display_end=duration-.04 if cue is meta['cues'][-1] else cue['end']
        text=cue['text'].replace('cinco segundos','<em>cinco segundos</em>').replace('conquistar clientes.','<em>conquistar clientes.</em>')
        # Phrase boundaries are exact generated audio boundaries.
        captions.append(f'''<div id="{cue['id']}" class="clip caption" data-start="{cue['start']}" data-duration="{display_end-cue['start']:.5f}"><div class="caption-text">{text}</div></div>''')
    brand=next(c for c in meta['cues'] if c['text']=='Umbrella.')
    (PROJECT/'index.html').write_text(f'''<!doctype html>
<html lang="pt-BR" data-composition-variables='[{{"id":"brand","type":"string","label":"Marca","default":"Umbrella"}}]'>
<head><meta charset="utf-8"><title>Umbrella — o contato</title>
<script src="assets/gsap.min.js"></script>
<style>html,body{{margin:0;width:1080px;height:1920px;background:#252127;overflow:hidden}}#root{{position:relative;width:1080px;height:1920px}}#continuous-take{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:contain;z-index:1}}#captions{{position:absolute;inset:0;z-index:2}}#identity{{position:absolute;inset:0;z-index:3}}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-fps="24" data-width="1080" data-height="1920">
<video id="continuous-take" class="clip" data-start="0" data-duration="{duration}" data-track-index="0" src="assets/continuous-take.mp4" muted playsinline></video>
<audio id="narration" class="clip" data-start="0" data-duration="{duration}" data-track-index="1" src="assets/narration.wav" data-volume="1"></audio>
<audio id="foley" class="clip" data-start="0" data-duration="{duration}" data-track-index="2" src="assets/foley.wav" data-volume="0.7"></audio>
<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{duration}" data-track-index="3" data-track-kind="captions" data-width="1080" data-height="1920"></div>
<div id="identity" data-composition-id="identity" data-composition-src="compositions/identity.html" data-start="0" data-duration="{duration}" data-track-index="4" data-track-kind="graphics" data-width="1080" data-height="1920"></div>
</div><script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});tl.to({{}},{{duration:{duration}}});window.__timelines.main=tl;</script></body></html>''',encoding='utf-8')
    (PROJECT/'compositions/captions.html').write_text('''<template><style>
@font-face{font-family:Manrope;src:url('assets/fonts/Manrope.ttf');font-weight:200 800}
#root{position:absolute;inset:0;pointer-events:none}
.caption{position:absolute;left:130px;top:386px;width:780px;text-align:center;color:#F5F3F7;font-family:Manrope;font-weight:600;font-size:66px;line-height:1.17;letter-spacing:-1.4px}
.caption-text{padding:10px 8px;text-shadow:0 2px 13px rgba(0,0,0,.4)}
em{font-style:normal;color:#CAB0FF;font-weight:750}
</style><div id="root" data-composition-id="captions" data-width="1080" data-height="1920">'''+''.join(captions)+'''</div><script>const tl=gsap.timeline({paused:true});'''+''.join(f"tl.fromTo('#{c['id']} .caption-text',{{opacity:0}},{{opacity:1,duration:0.08,ease:'none'}},{c['start']});" for c in meta['cues'] if c['text']!='Umbrella.')+'''window.__timelines.captions=tl;</script></template>''',encoding='utf-8')
    (PROJECT/'compositions/identity.html').write_text(f'''<template><style>
@font-face{{font-family:Manrope;src:url('assets/fonts/Manrope.ttf');font-weight:200 800}}
#root{{position:absolute;inset:0;pointer-events:none}}
#brand-title{{position:absolute;left:130px;top:242px;width:780px;text-align:center;color:#F5F3F7;font:600 116px/1.1 Manrope;letter-spacing:-4px}}
</style><div id="root" data-composition-id="identity" data-width="1080" data-height="1920"><div id="brand-title" class="clip" data-start="{brand['start']}" data-duration="{duration-brand['start']}"><div id="brand-text" data-var-text="brand">Umbrella</div></div></div>
<script>const tl=gsap.timeline({{paused:true}});tl.fromTo('#brand-text',{{opacity:0,y:14}},{{opacity:1,y:0,duration:.28,ease:'power2.out'}},{brand['start']});window.__timelines.identity=tl;</script></template>''',encoding='utf-8')
    return meta

def media(frames,ffmpeg,meta):
    # No cropping, digital zoom, reverse playback or camera cuts in finishing.
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-framerate','24',
                    '-i',str(frames/'frame-%04d.png'),'-frames:v',str(round(meta['duration']*24)),
                    '-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-vf',
                    'scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
                    '-movflags','+faststart',str(ASSETS/'continuous-take.mp4')],check=True)
    import assemble_v6
    import numpy as np
    import wave
    temp=ASSETS/'foley-v6-temp.wav'
    assemble_v6.audio_sketch(temp)
    with wave.open(str(temp),'rb') as w:
        audio=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2)
    # Retime each observed action independently, not a single global delay.
    target=np.arange(round(meta['duration']*48000))/48000
    old=np.interp(target,[0,5,5.38,5.65,6.00417,6.3625,15.35],
                  [0,4.9,5.0,5.29,5.65417,6.0125,15],left=0,right=16)
    source=np.arange(len(audio))/48000
    out=np.stack([np.interp(old,source,audio[:,c],left=0,right=0) for c in range(2)],axis=1).astype('<i2')
    start=round(5.70*48000)
    out[start:]=(out[start:].astype(float)*.35).astype('<i2')
    with wave.open(str(ASSETS/'foley.wav'),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(out.tobytes())
    temp.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--frames',type=Path);p.add_argument('--ffmpeg',default='ffmpeg')
    args=p.parse_args();meta=build()
    if args.frames:media(args.frames.resolve(),args.ffmpeg,meta)
    print('Editable local HyperFrames composition ready',meta['duration'])
