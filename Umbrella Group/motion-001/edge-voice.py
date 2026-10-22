"""Explicitly authorized online Edge voice test, without account or paid API."""
from pathlib import Path
import asyncio
import json
import argparse
import edge_tts

HERE=Path(__file__).resolve().parent
OUT=HERE/'edge-voice'
TEXT=('Você ficou cinco segundos esperando esse contato. '
      'Seu posicionamento precisa prender atenção e conquistar clientes. '
      'Umbrella. Conheça a Umbrella no perfil.')
REVISION_TEXT=('Você ficou cinco segundos esperando esse contato. '
      'Seu site também precisa causar impacto, prender atenção e conquistar clientes. '
      'É isso que a gente resolve. Conheça a Umbrella.')
async def generate(name,text,full=False,revision=False):
    voice=f'pt-BR-{name}Neural'
    short=name.lower()+('-v7-1' if revision else '-full' if full else '')
    audio=OUT/f'{short}.mp3'
    chunks=[]
    rate='+18%' if revision else '+3%'
    pitch='+4Hz' if revision else '+0Hz'
    stream=edge_tts.Communicate(text,voice,rate=rate,pitch=pitch,boundary='WordBoundary')
    with audio.open('wb') as f:
        async for chunk in stream.stream():
            if chunk['type']=='audio':f.write(chunk['data'])
            elif chunk['type']=='WordBoundary':chunks.append(chunk)
    (OUT/f'{short}.json').write_text(json.dumps({'provider':'Microsoft Edge online Read Aloud via edge-tts 7.3.1',
        'authorization':'User explicitly authorized a free no-account online test on 2026-10-22.',
        'voice':voice,'rate':rate,'pitch':pitch,'text':text,'boundaries':chunks},ensure_ascii=False,indent=2),encoding='utf-8')
    print(voice,'ready',audio.stat().st_size,flush=True)
async def main():
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--revision',action='store_true');a=p.parse_args()
    OUT.mkdir(exist_ok=True)
    for name in ('ThalitaMultilingual',) if a.revision else ('ThalitaMultilingual','Francisca'):
        await generate(name,REVISION_TEXT if a.revision else TEXT if a.full else TEXT.split('. ')[0]+'.',a.full,a.revision)
if __name__=='__main__':asyncio.run(main())
