"""Make the review proxy, inspect decoded files, and record measured delivery facts."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent

def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf-8',errors='replace')

def main():
    p=argparse.ArgumentParser();p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--version',default='v7',choices=['v7','v7-1'])
    a=p.parse_args();out=HERE/a.version;out.mkdir(exist_ok=True)
    master=out/f'motion-001-{a.version}-1080x1920.mp4';proxy=out/f'motion-001-{a.version}-540x960.mp4'
    meta=json.loads((HERE/'hyperframes-v7/assets/narration.json').read_text(encoding='utf-8'))
    if str(meta.get('voice_review','')).startswith('rejected'):
        raise ValueError('The current voice was rejected by the user. Replace it before delivery.')
    run([a.ffmpeg,'-v','error','-y','-i',str(master),'-vf','scale=540:960:flags=lanczos',
         '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(proxy)])
    records=[]
    for path,w,h in ((master,1080,1920),(proxy,540,960)):
        probe=json.loads(run([a.ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]).stdout)
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert (video['width'],video['height'])==(w,h)
        assert video['codec_name']=='h264' and video['r_frame_rate']=='24/1'
        assert int(video['nb_read_frames'])==round(meta['duration']*24)
        assert abs(float(probe['format']['duration'])-meta['duration'])<.1
        assert audio['codec_name']=='aac'
        assert all(video.get(k)=='bt709' for k in ('color_space','color_transfer','color_primaries'))
        # Fail on decode errors, including the audio track.
        decoded=run([a.ffmpeg,'-v','error','-xerror','-i',str(path),'-map','0:v:0','-map','0:a:0','-f','null','-'])
        assert not decoded.stderr.strip(),decoded.stderr
        records.append({'file':path.name,'bytes':path.stat().st_size,
                        'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),
                        'video':video,'audio':audio,'full_decode':'passed, no errors'})
    selected=(0,.5,2.5,4.5,5,5.42,5.7,7,10,11.5,14,15.5,18.5,20)
    thumbs=[]
    for t in selected:
        dest=out/f'review-{t:g}.png'
        run([a.ffmpeg,'-v','error','-y','-ss',str(t),'-i',str(master),'-frames:v','1',str(dest)])
        with Image.open(dest) as raw:
            tile=raw.convert('RGB').resize((216,384),Image.Resampling.LANCZOS)
        ImageDraw.Draw(tile).text((8,8),f'{t:g} s',fill='white',stroke_width=1,stroke_fill='black')
        thumbs.append(tile)
    sheet=Image.new('RGB',(7*216,2*384))
    for i,thumb in enumerate(thumbs):sheet.paste(thumb,((i%7)*216,(i//7)*384))
    sheet.save(out/'contact-sheet.png')
    report={'duration':meta['duration'],'fps':24,'frames':round(meta['duration']*24),
            'camera_count':1,'camera_cuts':0,'narration':meta,
            'files':records,'auditory_review':'Agent did not hear the final mix. User compared samples and selected Thalita; full-video approval remains pending.',
            'status':'Direction pilot, not approved for posting.'}
    if a.version=='v7-1':
        report.update(version='v7-1',
            status='User approved V7 visual direction; requested V7.1 copy, faster voice and flicker correction. Revised export pending user review.',
            auditory_review='User positively reviewed V7 with Thalita. Agent did not hear the revised V7.1 mix.',
            flicker_regression='See flicker-check.json; compares every decoded umbrella ROI frame from 12 s to end.')
    (out/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Two complete decoded videos verified.',flush=True)

if __name__=='__main__':main()
