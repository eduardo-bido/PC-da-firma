"""Check exported MP4s by fully decoding them; no ffprobe dependency."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

def verify(ffmpeg,folder):
    results=[]
    for width,height in ((1080,1920),(540,960)):
        path=folder/f'motion-001-v6-{width}x{height}.mp4'
        info=subprocess.run([str(ffmpeg),'-hide_banner','-i',str(path)],capture_output=True,text=True).stderr
        video=next((line.strip() for line in info.splitlines() if 'Video:' in line),'')
        audio=next((line.strip() for line in info.splitlines() if 'Audio:' in line),'')
        if f'{width}x{height}' not in video or 'h264' not in video or '24 fps' not in video:
            raise RuntimeError(f'Unexpected video format: {video}')
        if 'bt709' not in video or 'unknown/unknown' in video:
            raise RuntimeError(f'Unexpected color metadata: {video}')
        if 'aac' not in audio or '48000 Hz' not in audio or 'stereo' not in audio:
            raise RuntimeError(f'Unexpected audio format: {audio}')
        match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',info)
        duration=int(match[1])*3600+int(match[2])*60+float(match[3])
        if abs(duration-15)>.05:
            raise RuntimeError(f'Unexpected duration: {duration}')
        decoded=subprocess.run([str(ffmpeg),'-hide_banner','-v','error','-xerror',
                                '-i',str(path),'-map','0:v:0','-map','0:a:0',
                                '-progress','pipe:1','-nostats','-f','null','-'],
                               capture_output=True,text=True)
        decoded.check_returncode()
        counts=re.findall(r'^frame=(\d+)',decoded.stdout,re.M)
        if not counts or int(counts[-1])!=360:
            raise RuntimeError(f'Expected 360 decoded frames: {counts[-1:]!r}')
        results.append({'file':path.name,'bytes':path.stat().st_size,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'duration_s':duration,'decoded_frames':360,
                        'video':video,'audio':audio,'decode_errors':decoded.stderr.strip()})
    report={'version':'v6','outputs':results,
            'audio_source':'CC0 recording by bewareofkites20 plus procedural contact and cloth details; source/audio/LICENSE.txt',
            'identity':'LP reconstruction in review; documents 01 > 02 > 03 retain authority.',
            'visual_review':'Complete reduced playback and sampled inspection of contact, opening, print and copy. No measured audience retention or conversion result.',
            'limitations':'Art-directed opening and reduced support-body physics; no cloth self-collision or measured mass model.'}
    (folder/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--ffmpeg',type=Path,required=True)
    p.add_argument('--out',type=Path,default=Path('motion-001/v6'))
    args=p.parse_args()
    verify(args.ffmpeg.resolve(),args.out.resolve())
