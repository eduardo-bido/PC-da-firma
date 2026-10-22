"""Offline female voice design. Generate complete sentences, preserving prosody."""
from pathlib import Path
import argparse
import json
import os
import time
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

HERE=Path(__file__).resolve().parent
SENTENCES=[
    'Você ficou cinco segundos esperando esse contato.',
    'Seu posicionamento precisa prender atenção e conquistar clientes.',
    'Umbrella.',
    'Conheça a Umbrella no perfil.',
]
DIRECTION=('A Brazilian woman in her early thirties, native Brazilian Portuguese, '
    'warm clear mid-range female voice. Speak as a confident creative professional '
    'talking directly to one person, with connected phrasing, subtle expressive '
    'intonation and a relaxed smile. Conversational, engaging and brisk, '
    'not an announcer, not theatrical, not whispered. Natural Brazilian accent. '
    'A short social media voiceover, about 180 words per minute.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audition',action='store_true');a=p.parse_args()
    torch.manual_seed(42)
    torch.set_num_threads(8)
    out=HERE/'raw';out.mkdir(exist_ok=True)
    print('Loading local voice model, CUDA SDPA BF16.',flush=True)
    model=Qwen3TTSModel.from_pretrained(str(HERE/'model'),device_map='cuda:0',
        dtype=torch.bfloat16,attn_implementation='sdpa')
    texts=SENTENCES[:1] if a.audition else [' '.join(SENTENCES)]
    records=[]
    for i,text in enumerate(texts):
        start=time.monotonic()
        wavs,sr=model.generate_voice_design(text=text,language='Portuguese',
            instruct=DIRECTION,max_new_tokens=600,do_sample=True,temperature=.75,
            top_p=.9,repetition_penalty=1.08)
        samples=np.asarray(wavs[0],dtype=np.float32)
        active=np.flatnonzero(np.abs(samples)>.003)
        if len(active):samples=samples[max(0,active[0]-round(.04*sr)):active[-1]+round(.08*sr)]
        sf.write(out/f'sentence-{i+1}.wav',samples,sr,subtype='PCM_16')
        records.append({'text':text,'file':f'sentence-{i+1}.wav','duration':len(samples)/sr,'rate':sr})
        (out/'sentences.json').write_text(json.dumps({'direction':DIRECTION,'seed':42,
            'sentences':records},indent=2,ensure_ascii=False),encoding='utf-8')
        print(i+1,round(len(samples)/sr,3),'seconds; inference',round(time.monotonic()-start,1),flush=True)
