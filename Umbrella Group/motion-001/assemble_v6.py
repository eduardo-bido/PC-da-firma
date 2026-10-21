"""Local editorial finishing: Manrope, staged message, stereo placeholder foley."""
from __future__ import annotations
import argparse
import functools
import json
import math
import subprocess
import wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS, COUNT, RATE = 24, 360, 48000

def ease(x):
    x = np.clip(x,0,1)
    return 1-(1-x)**3

def opacity(t,start,end):
    return float(ease((t-start)/.20) * ease((end-t)/.16))

@functools.lru_cache(maxsize=32)
def font(path,size,weight):
    f=ImageFont.truetype(str(path),size)
    f.set_variation_by_axes([weight])
    return f

def lettered(frame,index,font_path):
    t=index/FPS
    w,h=frame.size
    scale=w/1080
    layer=Image.new('RGBA',(w,h))
    draw=ImageDraw.Draw(layer)
    color=(245,243,247)
    def text(lines,y,size,weight,start,end,spacing=1.19):
        alpha=opacity(t,start,end)
        if alpha<=0:
            return
        f=font(str(font_path),round(size*scale),weight)
        dy=(1-float(ease((t-start)/.28)))*18*scale
        for row,line in enumerate(lines):
            length=draw.textlength(line,font=f)
            draw.text(((w-length)/2,y*h+row*size*scale*spacing+dy),line,font=f,
                      fill=(*color,round(255*alpha)))
    # Each statement has its own reading window. The brand insert stays clear.
    text(['Você esperou','a queda.'],.145,76,600,5.48,6.83)
    text(['Seu site também','precisa prender.'],.145,72,600,8.54,10.62)
    text(['E converter.'],.174,88,650,10.62,11.82)
    text(['Umbrella'],.135,110,600,11.86,15.3)
    text(['Products that scale,','solutions that fit.'],.225,38,400,12.05,15.3,1.28)
    a=opacity(t,12.12,15.3)
    if a>0:
        label='Conheça a Umbrella no perfil'
        f=font(str(font_path),round(37*scale),550)
        length=draw.textlength(label,font=f)
        top=.787*h
        draw.rounded_rectangle(((w-length)/2-30*scale,top-18*scale,
                                (w+length)/2+30*scale,top+61*scale),
                               radius=38*scale,fill=(132,54,236,round(245*a)))
        draw.text(((w-length)/2,top),label,font=f,fill=(*color,round(255*a)))
    return Image.alpha_composite(frame.convert('RGBA'),layer).convert('RGB')

def audio_sketch(path):
    """CC0 recorded umbrella opening plus locally synthesized contact details."""
    rng=np.random.default_rng(1006)
    n=RATE*15
    time=np.arange(n)/RATE
    noise=rng.standard_normal(n)
    def avg(x,count):
        return np.convolve(x,np.ones(count)/count,mode='same')
    broad=avg(noise,7)-avg(noise,120)
    low=avg(noise,105)
    fine=noise-avg(noise,4)
    mono=np.zeros(n)
    # Discrete cloth transients avoid a constant white-noise bed.
    for at,gain,width in ((0,.10,.21),(.62,.035,.18),(1.25,.06,.17),(2.5,.045,.22)):
        d=time-at
        env=np.where(d>=0,np.exp(-np.maximum(d,0)/width),0)
        mono+=gain*env*broad
    velocity=.012+.016*np.sin(np.minimum(time,3.35)/3.35*np.pi/2)
    mono+=velocity*low*(1-ease((time-3.3)/.2))
    def contact(at,gain,decay=.05):
        nonlocal mono
        d=np.maximum(0,time-at)
        env=(time>=at)*np.exp(-d/decay)
        # Several weak resonances imitate a cap rather than a pure synth note.
        body=(.44*np.sin(2*np.pi*183*d)*np.exp(-d*26)
             +.21*np.sin(2*np.pi*521*d)*np.exp(-d*60)
             +.09*np.sin(2*np.pi*1173*d)*np.exp(-d*110))
        mono+=gain*env*(.72*broad+.24*fine+body)
    contact(4.9,.58,.047)
    contact(5.0,.24,.021)
    # Fast fabric expansion, spring latch and a long dry settling tail.
    d=np.maximum(0,time-5.025)
    open_env=(time>=5.025)*(1-np.exp(-d*45))*np.exp(-d*6.8)
    mod=.72+.28*np.sin(2*np.pi*(39*d+31*d*d))**2
    mono+=.16*open_env*mod*broad+.015*open_env*fine
    recorded=Path(__file__).resolve().parent/'source/audio/umbrella-opening-148918-cc0.wav'
    with wave.open(str(recorded),'rb') as wav:
        if wav.getframerate()!=RATE or wav.getnchannels()!=1 or wav.getsampwidth()!=2:
            raise ValueError('Recorded opening must be 48 kHz mono 16-bit PCM')
        sample=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)/32768
    sample=sample[round(.68*RATE):]
    sample*=ease(np.arange(len(sample))/(RATE*.008))*ease((len(sample)-np.arange(len(sample)))/(RATE*.045))
    at=round(5.02*RATE)
    mono[at:at+len(sample)]+=sample*1.45
    contact(5.29,.28,.028)
    contact(5.65417,.16,.055)
    contact(6.0125,.10,.04)
    for at,gain in ((5.37,.035),(5.75,.022),(6.13,.014)):
        d=np.maximum(0,time-at)
        mono+=gain*(time>=at)*np.exp(-d*3.5)*broad*(.6+.4*np.sin(d*90)**2)
    mono*=ease(time/.008)*ease((15-time)/.1)
    # Short room reflections and a narrow stereo image keep the impact centred.
    def delayed(seconds):
        samples=round(seconds*RATE)
        return np.pad(mono[:-samples],(samples,0))
    left=mono+.10*delayed(.021)+.045*delayed(.049)
    right=mono+.09*delayed(.026)+.04*delayed(.057)
    stereo=np.stack((left,right),axis=1)
    stereo*=.86/max(.001,np.abs(stereo).max())
    pcm=(np.clip(stereo,-.98,.98)*32767).astype('<i2')
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(pcm.tobytes())

def assemble(args):
    frames,out=args.frames.resolve(),args.out.resolve()
    for i in range(COUNT):
        if not (frames/f'frame-{i:04d}.png').is_file():
            raise FileNotFoundError(f'Missing frame {i}')
    out.mkdir(parents=True,exist_ok=True)
    first=Image.open(frames/'frame-0000.png')
    w,h=first.size
    wav=out/'sound-mix.wav'
    audio_sketch(wav)
    dest=out/f'motion-001-v6-{w}x{h}.mp4'
    cmd=[str(args.ffmpeg),'-hide_banner','-loglevel','error','-y','-f','rawvideo',
         '-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(FPS),'-i','-','-i',str(wav),
         '-map','0:v:0','-map','1:a:0','-frames:v',str(COUNT),'-c:v','libx264',
         '-crf','17','-preset','medium','-vf',
         'scale=out_color_matrix=bt709:out_range=tv,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
         '-pix_fmt','yuv420p','-color_primaries','bt709',
         '-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k',
         '-af','alimiter=limit=0.95:level=false','-movflags','+faststart',str(dest)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    tiles=[]
    selected=(0,24,54,80,104,118,126,140,176,210,240,267,304,336,359)
    for i in range(COUNT):
        with Image.open(frames/f'frame-{i:04d}.png') as raw:
            frame=lettered(raw,i,args.font.resolve())
        proc.stdin.write(frame.tobytes())
        if i in selected:
            tile=frame.resize((216,384),Image.Resampling.LANCZOS)
            ImageDraw.Draw(tile).text((8,8),f'{i/FPS:.2f}s',fill='white',stroke_width=1,stroke_fill='black')
            tiles.append(tile)
        if i==336:
            frame.save(out/'hero-frame.png')
    proc.stdin.close()
    error=proc.stderr.read().decode('utf-8','replace')
    if proc.wait():
        raise RuntimeError(error)
    sheet=Image.new('RGB',(216*5,384*3))
    for i,tile in enumerate(tiles):
        sheet.paste(tile,((i%5)*216,(i//5)*384))
    sheet.save(out/'contact-sheet.png')
    if w>540:
        preview=out/'motion-001-v6-540x960.mp4'
        subprocess.run([str(args.ffmpeg),'-hide_banner','-loglevel','error','-y','-i',str(dest),
                        '-vf','scale=540:960:flags=lanczos','-c:v','libx264','-crf','18',
                        '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(preview)],check=True)
    print(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--frames',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--ffmpeg',type=Path,required=True)
    p.add_argument('--font',type=Path,default=Path('public/fonts/Manrope.ttf'))
    assemble(p.parse_args())
