"""Revised cinematic SFX after user rejected the distant first sound sketch.

Public CC0 authored whoosh/cloth recordings + local dry transients/pressure.
The user explicitly requested suction, a strong opening, close bounces and rolls.
"""
from pathlib import Path
import argparse
import json
import subprocess
import wave
import numpy as np

HERE=Path(__file__).resolve().parent
RATE=48000
FFMPEG='ffmpeg'
def read(path,rate=RATE):
    r=subprocess.run([FFMPEG,'-v','error','-i',str(path),'-ar',str(rate),'-ac','2',
        '-f','f32le','pipe:1'],capture_output=True,check=True)
    return np.frombuffer(r.stdout,dtype='<f4').reshape(-1,2).astype(float)
def write(path,x):
    if x.ndim==1:x=np.stack((x,x),axis=1)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(np.rint(np.clip(x,-1,32767/32768)*32768).astype('<i2').tobytes())
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def filter_sound(x,low=55,high=4500):
    f=np.fft.rfftfreq(len(x),1/RATE)
    response=smooth((f-low*.5)/(low*.5))*(1-smooth((f-high)/(high*.35)))
    return np.fft.irfft(np.fft.rfft(x,axis=0)*response[:,None],n=len(x),axis=0)
def normalize(x,peak):return x*(peak/max(1e-8,np.abs(x).max()))
def stretch(x,seconds,pitch=1):
    tempo=len(x)/RATE/pitch/seconds;filters=[f'asetrate={RATE*pitch}',f'aresample={RATE}']
    while tempo<.5:filters.append('atempo=0.5');tempo/=.5
    while tempo>2:filters.append('atempo=2');tempo/=2
    filters.append(f'atempo={tempo:.8f}')
    r=subprocess.run([FFMPEG,'-v','error','-f','f32le','-ar',str(RATE),'-ac','2','-i','pipe:0',
        '-af',','.join(filters),'-f','f32le','pipe:1'],input=x.astype('<f4').tobytes(),capture_output=True,check=True)
    y=np.frombuffer(r.stdout,dtype='<f4').reshape(-1,2).astype(float)
    n=round(seconds*RATE)
    if len(y)<n:y=np.pad(y,((0,n-len(y)),(0,0)))
    return y[:n]
def handles(x,attack=.01,release=.025):
    t=np.arange(len(x))/RATE;return x*(smooth(t/attack)*(1-smooth((t-(len(x)/RATE-release))/release)))[:,None]
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ffmpeg',default='ffmpeg')
    FFMPEG=parser.parse_args().ffmpeg
    out=HERE/'v8';out.mkdir(exist_ok=True)
    n=round(481/24*RATE);mix=np.zeros((n,2));stems={}
    def put(name,sound,at,duck=True):
        signal=np.zeros_like(mix);i=round(at*RATE);stop=min(n,i+len(sound));sound=sound[:stop-i]
        if duck:
            t=(i+np.arange(len(sound)))/RATE
            sound=sound*(1-.58*smooth((t-5.70)/.12))[:,None]
        signal[i:stop]+=sound;stems[name]=signal;mix[:]+=signal
    source=HERE/'source/audio'
    whoosh=filter_sound(read(source/'cinematic-whoosh-729226-cc0.mp3'),45,6500)
    zwoop=filter_sound(read(source/'whoosh-click-108334-cc0.mp3'),80,6000)
    wobble=filter_sound(read(source/'placemat-wobble-444771-cc0.mp3'),70,1800)
    opening=read(source/'umbrella-opening-148918-cc0.wav')
    put('initial_visible_drop',handles(normalize(stretch(whoosh[:round(.75*RATE)],.40,.9),.42),.008,.06),0)
    # Reversing the decay gives an authored cinematic intake, ending at the gap.
    intake=stretch(whoosh[round(.43*RATE):round(1.70*RATE)][::-1].copy(),4.45,.85)
    t=np.arange(len(intake))/RATE
    intake=normalize(intake,.66)*(.35+.65*smooth(t/4.15))[:,None]
    put('cinematic_suction',handles(intake,.08,.035),.43)
    zip_sound=normalize(stretch(zwoop[:round(.43*RATE)][::-1].copy(),.73,.88),.32)
    put('suction_focus_zwoop',handles(zip_sound,.025,.035),4.15)
    # Deep but mobile-audible pressure rise; harmonics carry it on small speakers.
    rng=np.random.default_rng(8882)
    tt=np.arange(round(4.4*RATE))/RATE;u=smooth(tt/4.4)
    frequency=68+128*u
    phase=2*np.pi*np.cumsum(frequency)/RATE
    pressure=(np.sin(phase)+.35*np.sin(2.03*phase)+.16*np.sin(3.1*phase))
    pressure*=.045*u**1.7*smooth(tt/.2)*(1-smooth((tt-4.27)/.13))
    put('pressure_under_suction',np.stack((pressure,pressure),axis=1),.48)
    def thump(at,peak,decay=.085):
        length=.28;t=np.arange(round(length*RATE))/RATE
        white=rng.standard_normal(len(t));stereo=np.stack((white,white),axis=1)
        knock=filter_sound(stereo,90,2200)[:,0]
        knock/=max(1e-8,np.sqrt(np.mean(knock**2)))
        body=np.sin(2*np.pi*(120*t-75*t*t))*np.exp(-t/decay)
        mid=.35*np.sin(2*np.pi*245*t)*np.exp(-t/.019)
        dry=.22*knock*np.exp(-t/.016)
        sound=(body+mid+dry)*smooth(t/.0008)*(1-smooth((t-.22)/.06))
        return normalize(np.stack((sound,sound*.98),axis=1),peak)
    put('tip_contact_close',thump(5,.80,.055),5,False)
    # The real umbrella opening supplies the recognizable cloth and latch detail.
    snap=filter_sound(opening[round(.60*RATE):round(1.13*RATE)],55,9000)
    snap=handles(normalize(stretch(snap,.46,.92),.76),.004,.025)
    put('real_umbrella_blauf',snap,5.31,False)
    expansion=normalize(stretch(whoosh[round(.16*RATE):round(.65*RATE)],.27,.7),.29)
    put('canopy_air_expansion',handles(expansion,.012,.08),5.38,False)
    put('opening_body',thump(5.4,.25,.09),5.40,False)
    # Two strong support changes and a soft final settling touch, all close/dry.
    for j,(at,peak) in enumerate(((6.00417,.66),(6.3625,.49),(6.70,.24))):
        put(f'bounce_poc_{j+1}',thump(at,peak,.055),at)
    for j,(at,length,peak) in enumerate(((5.82,.76,.31),(6.66,1.02,.22),(7.60,.82,.11))):
        rough=stretch(wobble[round(.65*RATE):round(2.1*RATE)],length,.70)
        rough=normalize(rough,peak)
        tt=np.arange(len(rough))/RATE
        rough*=((.65+.35*np.sin(2*np.pi*(18*tt+5*tt*tt))**2)
            *smooth(tt/.04)*(1-smooth((tt-length+.18)/.18)))[:,None]
        # Keep a small left/right movement; every cue remains audible in mono.
        rough[:,j%2]*=.88
        put(f'rolling_rrruom_{j+1}',rough,at)
    pre=round(4.92*RATE);hit=round(5*RATE)
    mix[pre:hit]=0
    peak=float(np.abs(mix).max());gain=min(1,.94/peak);mix*=gain
    write(HERE/'hyperframes-v8/assets/foley.wav',mix)
    # Actual balance with the approved voice, not just isolated oversized SFX.
    voice=read(HERE/'hyperframes-v8/assets/narration.wav')
    audition=mix*.7+voice
    top=np.abs(audition).max()
    if top>.96:audition*=.96/top
    write(out/'sound-cinema-v2.wav',audition[:round(9.5*RATE)])
    for name,signal in stems.items():
        if name in ('cinematic_suction','real_umbrella_blauf','bounce_poc_1','rolling_rrruom_1'):
            write(out/f'stem-{name}.wav',signal[:round(9.5*RATE)]*gain)
    report={'version':'cinema-v2','replaces':'Rejected V8 distant filtered-noise sketch',
        'user_direction':'zuuuup suction; blauf canopy; poc poc poc close bounces; rrruom rolling',
        'authored_cc0_sources':['KVV_Audio/729226','Qat/108334','jackhilton/444771','bewareofkites20/148918'],
        'sfx_bus_gain':gain,'sfx_peak_dbfs':float(20*np.log10(np.abs(mix).max())),
        'final_mix_peak_dbfs':float(20*np.log10(np.abs(audition).max())),
        'final_mix_gain':float(.96/top if top>.96 else 1),
        'silent_gap':[4.92,5.0],'narration':'Exact approved V7.1 file; SFX duck 58% during speech.',
        'events':[{'stem':k,'peak_dbfs':float(20*np.log10(max(1e-12,np.abs(v*gain).max())))} for k,v in stems.items()],
        'qualification':'Third soft settling touch is stylized sound design; rigid-body motion is unchanged. Agent has not listened; audition sent to user.'}
    (out/'sound-design.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Cinema v2 built',round(20*np.log10(np.abs(mix).max()),2),'dBFS; no clipping.',flush=True)
