"""V8 sound revision from the exact slow-motion clip selected by the user.

No synthesized contact, tonal pressure, pitch shifting or time stretching.
The selected YouTube effect has no reuse license in its public description;
keep that provenance distinct from the separately verified CC0 Foley sources.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import design_v8_cinema as audio

HERE=Path(__file__).resolve().parent
RATE=48000

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--ffmpeg',default='ffmpeg')
    p.add_argument('--reference',type=Path,default=HERE/'source/audio/reference-slow-motion-z_epWpdsHJc.m4a')
    args=p.parse_args()
    if not args.reference.is_file():
        p.error('Reference audio is local only and not distributed in Git. Supply --reference with a local file authorized for your intended use.')
    audio.FFMPEG=args.ffmpeg
    out=HERE/'v8';out.mkdir(exist_ok=True)
    source=HERE/'source/audio'
    mix=np.zeros((962000,2));events=[]

    def put(name,x,at,peak,duck=True):
        x=audio.handles(audio.normalize(x,peak),.003,.035)
        start=round(at*RATE);end=min(len(mix),start+len(x));x=x[:end-start]
        if duck:
            t=(start+np.arange(len(x)))/RATE
            x=x*(1-.44*audio.smooth((t-5.70)/.12))[:,None]
        mix[start:end]+=x
        events.append({'stem':name,'at':at,'duration':len(x)/RATE,
                       'peak_dbfs':float(20*np.log10(np.abs(x).max()))})

    reference=audio.read(args.reference)
    # Preserve the selected clip's timing/timbre, including its own internal gap.
    put('exact_user_slow_motion_reference',reference,.65,.74,False)
    air=audio.read(source/'cinematic-whoosh-729226-cc0.mp3')
    put('initial_drop_recorded_air',air[:round(.40*RATE)],0,.37,False)

    hits=audio.read(source/'wooden-object-thuds-732684-cc0.mp3')
    def recorded_hit(left,right):
        x=hits[round(left*RATE):round(right*RATE)]
        envelope=np.abs(x).max(axis=1)
        onset=np.where(envelope>envelope.max()*.12)[0][0]
        return x[max(0,onset-48):]
    put('recorded_tip_contact',recorded_hit(.16,.72),5,.81,False)
    opening=audio.read(source/'umbrella-opening-148918-cc0.wav')
    put('real_umbrella_blauf',opening[round(.60*RATE):round(1.13*RATE)],5.30,.83,False)
    for name,left,right,at,peak in (
        ('bounce_poc_1',.85,1.3,6.00417,.57),
        ('bounce_poc_2',1.34,1.84,6.3625,.41),
        ('bounce_poc_3',2.14,2.65,6.70,.19)):
        put(name,recorded_hit(left,right),at,peak)

    roll=audio.read(source/'placemat-wobble-444771-cc0.mp3')
    put('rolling_rrruom_1',roll[round(.65*RATE):round(1.35*RATE)],5.83,.24)
    put('rolling_rrruom_2',roll[round(1.4*RATE):round(2.1*RATE)],6.70,.16)
    put('rolling_rrruom_3',roll[round(2.3*RATE):round(2.85*RATE)],7.60,.065)

    mix[round(4.92*RATE):5*RATE]=0
    bus_gain=min(1,.94/np.abs(mix).max());mix*=bus_gain
    audio.write(HERE/'hyperframes-v8/assets/foley.wav',mix)
    voice=audio.read(HERE/'hyperframes-v8/assets/narration.wav')
    audition=mix*.7+voice
    assert np.abs(audition).max()<.98,'Adjust effects balance before export'
    audio.write(out/'sound-reference-v3.wav',audition[:round(9.5*RATE)])
    provenance={'title':'Slow Motion Sound Effect','uploader':'twonxd',
        'source':'https://www.youtube.com/watch?v=z_epWpdsHJc',
        'selected_by_user':True,'license':'Not specified in the public description; not CC0 verified',
        'checked':'2026-10-23','sha256':hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        'local_file':args.reference.name,'source_duration':len(reference)/RATE}
    (source/'reference-slow-motion-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    report={'version':'reference-v3','replaces':'cinema-v2 rejected by user as robotic',
        'reference':provenance,'reference_start':.65,'reference_pitch_and_tempo':'unchanged',
        'synthetic_pressure_and_impacts':False,'silent_gap':[4.92,5.0],
        'sfx_bus_gain':float(bus_gain),'sfx_peak_dbfs':float(20*np.log10(np.abs(mix).max())),
        'final_mix_peak_dbfs':float(20*np.log10(np.abs(audition).max())),
        'narration':'Exact approved V7.1 file; effects duck 44% during speech',
        'events':events,'qualification':'Third touch is stylized settling. Agent did not hear the mix. Reference reuse license remains unverified.'}
    (out/'sound-design.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Exact-reference sound ready; unmodified pitch/tempo; sample peak',round(report['final_mix_peak_dbfs'],2),'dBFS',flush=True)
