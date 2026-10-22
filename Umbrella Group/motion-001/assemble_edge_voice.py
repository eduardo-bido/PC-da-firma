"""Finish the selected Edge recording offline, using supplied word boundaries."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import unicodedata
import wave

HERE=Path(__file__).resolve().parent
OUT=HERE/'hyperframes-v7/assets'
START=5.76
DURATION=481/24
GROUPS=['Você ficou cinco segundos','esperando esse contato.',
    'Seu posicionamento precisa','prender atenção e conquistar clientes.',
    'Umbrella.','Conheça a Umbrella no perfil.']
REVISION_GROUPS=['Você ficou cinco segundos','esperando esse contato.',
    'Seu site também precisa','causar impacto,','prender atenção',
    'e conquistar clientes.','É isso que a gente resolve.','Conheça a Umbrella.']
def norm(s):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFD',s.lower()).encode('ascii','ignore').decode())
def stamp(s):
    m=round(s*1000);h,m=divmod(m,3600000);mi,m=divmod(m,60000);se,m=divmod(m,1000)
    return f'{h:02}:{mi:02}:{se:02},{m:03}'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--revision',action='store_true');a=p.parse_args()
    if a.revision:GROUPS=REVISION_GROUPS
    source=HERE/('edge-voice/thalitamultilingual-v7-1.mp3' if a.revision else 'edge-voice/thalitamultilingual-full.mp3')
    data=json.loads(source.with_suffix('.json').read_text(encoding='utf-8'))
    words=data['boundaries'];expected=' '.join(GROUPS).split()
    if len(words)!=len(expected) or any(norm(w['text'])!=norm(t) for w,t in zip(words,expected)):
        raise ValueError('Service boundaries differ from exact script.')
    end=START+(words[-1]['offset']+words[-1]['duration'])/1e7
    if end>DURATION-.5:raise ValueError('Speech exceeds available picture.')
    cues=[];cursor=0
    for i,text in enumerate(GROUPS):
        n=len(text.split());part=words[cursor:cursor+n];cursor+=n
        cues.append({'id':f'caption-{i+1}','text':text,
            'start':round(START+part[0]['offset']/1e7,5),
            'end':round(START+(part[-1]['offset']+part[-1]['duration'])/1e7+.08,5)})
    for c,next_c in zip(cues,cues[1:]):c['end']=min(c['end'],next_c['start'])
    subprocess.run([a.ffmpeg,'-v','error','-y','-i',str(source),
        '-af','highpass=f=65,loudnorm=I=-17:TP=-1.5:LRA=9',
        '-ar','24000','-ac','1','-c:a','pcm_s16le',str(OUT/'voice-demo.wav')],check=True)
    # Explicit PCM padding avoids FFmpeg timestamp trimming the leading delay.
    with wave.open(str(OUT/'voice-demo.wav'),'rb') as w:
        speech=w.readframes(w.getnframes());rate=w.getframerate()
    leading=bytes(round(START*rate)*2)
    tail=bytes(round(DURATION*rate)*2-len(leading)-len(speech))
    with wave.open(str(OUT/'narration.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(leading+speech+tail)
    # Preserve a dry source without modifying the selected voice's rate or pitch.
    subprocess.run([a.ffmpeg,'-v','error','-y','-i',str(source),'-ar','24000','-ac','1',
        str(OUT/'narration-dry.wav')],check=True)
    meta={'voice':data['voice'],'lang':'pt-br','provider':data['provider'],
        'voice_review':'Thalita selected by user; V7 positively reviewed. V7.1 revises copy and makes speech faster as requested; full revised mix not yet auditioned.',
        'authorization':data['authorization'],'duration':DURATION,'fps':24,
        'speech_start':START,'speech_end':end,'rate':data['rate'],
        'pitch_preserving_tempo':1.0,
        'processing':'High-pass 65 Hz, loudness normalization -17 LUFS / -1.5 dBTP; no music. No post-generation time stretch.',
        'caption_alignment':'Actual service WordBoundary offsets, grouped into phrases; no estimated karaoke timing.',
        'cues':cues}
    (OUT/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.revision:
        meta.update(version='v7-1',pitch=data['pitch'],brand_start=cues[-1]['start'])
        (OUT/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'transcription.json').write_text(json.dumps({'source':'service word boundaries, not independent ASR',
        'words':words},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(cues))+'\n',encoding='utf-8')
    print('Selected Thalita voice assembled; speech ends',round(end,3),flush=True)
