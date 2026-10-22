"""Female pt-BR narration, generated locally with Kokoro; phrase-bound captions."""
from pathlib import Path
import json
import tempfile
import shutil
import subprocess
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
TMP = HERE / '.tmp'
TMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TMP)
OUT = HERE.parent / 'hyperframes-v7' / 'assets'
VOICE = 'pf_dora'
SPEED = 1.0
TEMPO = 1.08
TARGET_DURATION = 481/24
# Each caption is exactly the matching synthesized phrase, not an estimated
# word-by-word alignment. Sentence fragments are intentionally never karaoke.
PHRASES = [
    ('Você ficou cinco segundos', .04),
    ('esperando esse contato.', .34),
    ('Seu posicionamento também precisa', .035),
    ('prender atenção e conquistar clientes.', .34),
    ('Umbrella.', .10),
    ('Ajudando no seu posicionamento digital.', .32),
    ('Conheça a Umbrella no perfil.', .50),
]

class TypedSession:
    """0.4.9 assumes an integer speed for this export; obey ONNX metadata."""
    def __init__(self, session):
        self.session = session
        self.types = {i.name:i.type for i in session.get_inputs()}
    def get_inputs(self):
        return self.session.get_inputs()
    def run(self, outputs, inputs):
        dtypes = {'tensor(float)':np.float32, 'tensor(int64)':np.int64,
                  'tensor(int32)':np.int32}
        checked = {name:np.asarray(value,dtype=dtypes[self.types[name]])
                   for name,value in inputs.items()}
        return self.session.run(outputs,checked)

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    engine = Kokoro(str(HERE/'kokoro-v1.0.onnx'), str(HERE/'voices-v1.0.bin'))
    engine.sess = TypedSession(engine.sess)
    cursor = 5.76
    chunks = [np.zeros(round(cursor*24000), dtype=np.float32)]
    cues = []
    for i, (text, pause) in enumerate(PHRASES):
        # Phonetic spelling is confined to speech; on-screen brand stays exact.
        spoken = 'Âmbrela.' if text == 'Umbrella.' else text
        samples, rate = engine.create(spoken, voice=VOICE, speed=SPEED, lang='pt-br')
        if rate != 24000:
            raise ValueError('Unexpected model sample rate')
        # Trim only true edge silence, preserving 35 ms handles and all breaths.
        active = np.flatnonzero(np.abs(samples) > .003)
        if len(active):
            samples = samples[max(0, active[0]-840):min(len(samples),active[-1]+841)]
        ffmpeg=shutil.which('ffmpeg') or 'C:/Program Files/ShareX/ffmpeg.exe'
        stretched=subprocess.run([ffmpeg,'-v','error','-f','f32le','-ar','24000','-ac','1','-i','pipe:0',
                                   '-af',f'atempo={TEMPO}','-f','f32le','pipe:1'],
                                  input=np.asarray(samples,dtype='<f4').tobytes(),capture_output=True,check=True)
        samples=np.frombuffer(stretched.stdout,dtype='<f4')
        seconds = len(samples)/rate
        cues.append({'id': f'caption-{i+1}', 'text': text,
                     'start': round(cursor,5), 'end': round(cursor+seconds,5)})
        chunks.extend([samples, np.zeros(round(pause*rate), dtype=np.float32)])
        cursor += seconds + round(pause*rate)/rate
        print(i, text, round(seconds,3), flush=True)
    audio = np.concatenate(chunks)
    duration = TARGET_DURATION
    if len(audio)/24000 > duration-.2:
        raise ValueError(f'Voice exceeds the picture: {len(audio)/24000:.3f}s. Revise pacing rather than cutting speech.')
    audio = np.pad(audio, (0, round(duration*24000)-len(audio)))
    sf.write(OUT/'narration-dry.wav', audio, 24000, subtype='PCM_16')
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(OUT/'narration-dry.wav'),
                    '-af',f'highpass=f=80,acompressor=threshold=0.04:ratio=3:attack=5:release=80:makeup=3,loudnorm=I=-17:TP=-1.5:LRA=7,apad,atrim=end={duration}',
                    '-ar','24000','-ac','1',str(OUT/'narration.wav')],check=True)
    data = {'voice':VOICE, 'lang':'pt-br', 'provider':'Kokoro 82M / ONNX, offline',
            'voice_review':'rejected_by_user_2026-10-22_as_robotic; historical test only',
            'speed':SPEED, 'pitch_preserving_tempo':TEMPO, 'duration':float(duration), 'fps':24,
            'processing':'80 Hz high-pass, compressor, loudness normalization, -1.5 dBTP limit; no voice cloning.',
            'caption_alignment':'Exact generated phrase boundaries; no inferred word timing.',
            'cues':cues}
    (OUT/'narration.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    def stamp(s):
        ms=round(s*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{sec:02},{ms:03}'
    (OUT/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(cues))+'\n',encoding='utf-8')
    print('Duration', duration, flush=True)
