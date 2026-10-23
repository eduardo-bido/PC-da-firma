"""Stage only this explicit V8 delivery set in the existing Git checkout."""
from pathlib import Path
import shutil
import subprocess

root=Path(__file__).resolve().parents[2]
repo=root/'.git-delivery'
files=['.gitignore']
files+=['motion-001/'+n for n in (
    'README.md','CONTINUAR_AQUI.md','prepare_v7.py','finish_v7.py',
    'render_3d_v8.py','prepare_v8.py','design_v8_cinema.py','design_v8_reference.py','verify_v8.py',
    'diagnostics/sync_v8_checkpoint.py')]
files+=['motion-001/hyperframes-v8/'+n for n in (
    'README.md','package.json','package-lock.json','run.mjs','index.html',
    'compositions/captions.html','compositions/identity.html','check-report.json',
    'assets/fonts/Manrope.ttf','assets/gsap.min.js','assets/continuous-take.mp4',
    'assets/continuous-take.render.json','assets/narration.wav',
    'assets/narration-dry.wav','assets/voice-demo.wav','assets/narration.json',
    'assets/captions.srt','assets/transcription.json')]
files+=['motion-001/v8/'+n for n in (
    'README.md',
    'contact-sheet.png','first-second.png','late-continuity.png',
    'verification.json','creative-verification.json','audio-verification.json','layout-report.json','sound-design.json')]
files+=['motion-001/source/audio/'+n for n in (
    'fetch_v8_sfx.py','LICENSE-V8.md','v8-sfx-manifest.json',
    'cinematic-whoosh-729226-cc0.mp3','whoosh-click-108334-cc0.mp3',
    'placemat-wobble-444771-cc0.mp3','wooden-object-thuds-732684-cc0.mp3',
    'reference-slow-motion-provenance.json')]

paths=[]
for name in files:
    source=(root/name).resolve()
    target=(repo/'Umbrella Group'/name).resolve()
    if not source.is_relative_to(root) or not target.is_relative_to(repo):
        raise ValueError('Path outside intended delivery subtree')
    if not source.is_file():raise FileNotFoundError(source)
    if source.stat().st_size>=100_000_000:raise ValueError('Git file exceeds size gate')
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    paths.append('Umbrella Group/'+name)

tracked=set(subprocess.check_output(['git','-C',str(repo),'ls-files','-z']).decode().split('\0'))
existing=[n for n in paths if n in tracked]
if existing:
    subprocess.run(['git','-C',str(repo),'update-index','--no-skip-worktree','--',*existing],check=True)
subprocess.run(['git','-C',str(repo),'add','--',*paths],check=True)
print('Staged',len(paths),'explicit V8 files; no LP or unrelated project paths.')
