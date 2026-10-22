"""Fit the connected narration and caption actual ASR word boundaries locally."""
from pathlib import Path
import json
import os
import re
import subprocess
import unicodedata
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['HF_HUB_DISABLE_XET']='1'
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'hyperframes-v7/assets'
FFMPEG='C:/Program Files/ShareX/ffmpeg.exe'
START=5.76
DURATION=481/24
GROUPS=['Você ficou cinco segundos','esperando esse contato.',
    'Seu posicionamento precisa','prender atenção e conquistar clientes.',
    'Umbrella.','Conheça a Umbrella no perfil.']
def norm(s):
    return re.sub('[^a-z0-9]','',unicodedata.normalize('NFD',s.lower()).encode('ascii','ignore').decode())
def stamp(s):
    m=round(s*1000);h,m=divmod(m,3600000);mi,m=divmod(m,60000);se,m=divmod(m,1000)
    return f'{h:02}:{mi:02}:{se:02},{m:03}'
if __name__=='__main__':
    samples,rate=sf.read(HERE/'raw/sentence-1.wav')
    tempo=max(1,len(samples)/rate/(DURATION-START-.65))
    if tempo>1.12:raise ValueError(f'Voice too slow ({len(samples)/rate:.2f}s); regenerate, do not force speed.')
    demo=OUT/'voice-demo.wav'
    subprocess.run([FFMPEG,'-v','error','-y','-i',str(HERE/'raw/sentence-1.wav'),
        '-af',f'atempo={tempo:.8f},highpass=f=65,loudnorm=I=-17:TP=-1.5:LRA=9',
        '-ar','24000','-ac','1',str(demo)],check=True)
    print('Transcribing connected narration locally on CPU.',flush=True)
    model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=8,
        download_root=str(HERE/'cache'))
    segments,info=model.transcribe(str(demo),language='pt',word_timestamps=True,
        beam_size=5,condition_on_previous_text=False,vad_filter=False)
    words=[{'word':w.word.strip(),'start':w.start,'end':w.end,'probability':w.probability}
        for seg in segments for w in seg.words]
    (OUT/'transcription.json').write_text(json.dumps(words,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Recognized:', ' '.join(w['word'] for w in words),flush=True)
    expected=' '.join(GROUPS).split()
    # ASR verifies content and gives measured estimates; it does not prove naturalness.
    if len(words)!=len(expected) or any(norm(a['word'])!=norm(b) for a,b in zip(words,expected)):
        raise ValueError('ASR differs from script. Inspect transcription before accepting captions.')
    cues=[];cursor=0
    for i,text in enumerate(GROUPS):
        n=len(text.split());part=words[cursor:cursor+n];cursor+=n
        cues.append({'id':f'caption-{i+1}','text':text,
            'start':round(START+part[0]['start'],5),'end':round(START+part[-1]['end']+.05,5)})
    for a,b in zip(cues,cues[1:]):a['end']=min(a['end'],b['start'])
    speech,sr=sf.read(demo);audio=np.zeros(round(DURATION*sr),dtype=np.float32)
    begin=round(START*sr);audio[begin:begin+len(speech)]=speech
    sf.write(OUT/'narration.wav',audio,sr,subtype='PCM_16')
    sf.write(OUT/'narration-dry.wav',np.pad(samples,(round(START*rate),max(0,round(DURATION*rate)-round(START*rate)-len(samples)))),rate,subtype='PCM_16')
    meta={'voice':'designed female Brazilian Portuguese; seed 42','lang':'pt-br',
        'provider':'Qwen3-TTS 1.7B VoiceDesign, offline CUDA SDPA BF16',
        'voice_review':'new replacement audition; not heard by agent or approved by user',
        'duration':DURATION,'fps':24,'pitch_preserving_tempo':tempo,
        'processing':'High-pass 65 Hz, loudness normalization -17 LUFS / -1.5 dBTP; no music or real-person cloning.',
        'caption_alignment':'Faster-whisper small word timestamps, grouped phrases; automatic estimates, transcript compared to script.',
        'cues':cues}
    (OUT/'narration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(cues))+'\n',encoding='utf-8')
    print('Voice and captions ready',len(speech)/sr,flush=True)
