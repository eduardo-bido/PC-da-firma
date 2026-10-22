"""Inspect sign continuity of the baked transforms around visible flashes."""
from pathlib import Path
import sys
import json
import bpy
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import render_3d_v7 as shot
rig,cam,scene=shot.look.scene_setup(270,480,8)
root=rig['root'];root.rotation_mode='QUATERNION'
samples=[]
for frame in range(288,482):
    state=shot.motion.apply_motion(frame/24,rig)
    shot.camera_pose(frame/24,state,cam,481/24)
    q=list(root.rotation_quaternion)
    c=list(cam.rotation_quaternion)
    samples.append({'frame':frame,'root':q,'camera':c,'tilt':state['tilt']})
events=[]
for a,b in zip(samples,samples[1:]):
    dot=sum(x*y for x,y in zip(a['root'],b['root']))
    if dot<.9:events.append({'before':a,'after':b,'dot':dot})
out=HERE/'diagnostics/v7-quaternion-audit.json'
out.write_text(json.dumps({'events':events,'samples':samples},indent=2),encoding='utf-8')
print('SIGN_EVENTS',json.dumps(events),flush=True)
