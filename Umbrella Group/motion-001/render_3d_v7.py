"""One physical camera, one uncut take; no animated lens or 2D scale.

Reuses the documented LP reconstruction, not a recovered brand master.
The camera tracks the actual shaft tip until contact, then withdraws along
the same azimuth so opening, support and the printed mark remain one event.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_3d_v6 as previous
look, motion = previous.look, previous.motion
FPS=24

# A lower release keeps the floor and a large object in the initial framing.
motion.FALL_HEIGHT=.82
motion.CONTACT_TIME=5.0
motion.OPEN_START=5.38
motion.OPEN_END=5.65
motion.SETTLE_START=5.65
motion._PHYSICAL_HIT=(-motion.FALL_INITIAL_SPEED+math.sqrt(
    motion.FALL_INITIAL_SPEED**2+2*motion.GRAVITY*motion.FALL_HEIGHT))/motion.GRAVITY

def fall_clock(t):
    p=motion._PHYSICAL_HIT
    times=(0,1.6,3.4,5.0)
    values=(0,.48*p,.90*p,p)
    slopes=(.28*p,.24*p,.055*p,.018*p)
    t=min(5,max(0,t))
    i=next((i for i in range(3) if t<=times[i+1]),2)
    d=times[i+1]-times[i];u=(t-times[i])/d
    return ((2*u**3-3*u*u+1)*values[i]+(u**3-2*u*u+u)*d*slopes[i]
            +(-2*u**3+3*u*u)*values[i+1]+(u**3-u*u)*d*slopes[i+1])
motion.fall_clock=fall_clock

def smooth5(x):
    x=min(1,max(0,x))
    return x*x*x*(10-15*x+6*x*x)

def camera_pose(t,state,cam,duration):
    az=math.radians(-35)
    if t<=5.0:
        u=smooth5(t/5)
        # A log distance ramp makes the approach perceptually controlled.
        distance=math.exp(math.log(2.20)*(1-u)+math.log(.38)*u)
        height=state['tip_position'].z + .19*(1-u)+.027*u
        target=Vector((0,0,height))
        elevation=.25*(1-u)+.16*u
        focus=state['tip_position']+Vector((0,0,.015))
    else:
        # Withdraw early enough to show the linkage expanding in the same take.
        u=smooth5((t-5)/.75)
        distance=math.exp(math.log(.38)*(1-u)+math.log(3.02)*u)
        target=Vector((0,0,.027*(1-u)+.67*u))
        elevation=.16*(1-u)+.245*u
        focus=state['tip_position'].lerp(state['brand_focus'],u)
        # Very small continuing approach; no frozen illustration under the VO.
        late=smooth5((t-7)/max(1,duration-7))
        distance*=1-.055*late
    cam.location=target+Vector((math.cos(az)*distance*math.cos(elevation),
                               math.sin(az)*distance*math.cos(elevation),
                               distance*math.sin(elevation)))
    cam.rotation_mode='QUATERNION'
    cam.rotation_quaternion=(target-cam.location).to_track_quat('-Z','Y')
    cam.data.sensor_fit='HORIZONTAL'
    cam.data.lens=50
    cam.data.dof.aperture_fstop=11
    cam.data.dof.focus_distance=(cam.location-focus).length

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--frames',default='0,12,48,80,104,118,120,125,129,138,150,168,240,400')
    p.add_argument('--all',action='store_true')
    p.add_argument('--start',type=int,default=0)
    p.add_argument('--end',type=int)
    p.add_argument('--width',type=int,default=540)
    p.add_argument('--height',type=int,default=960)
    p.add_argument('--samples',type=int,default=24)
    p.add_argument('--resume',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.out=a.out.resolve()
    metadata=json.loads((HERE/'hyperframes-v7/assets/narration.json').read_text(encoding='utf-8'))
    count=round(metadata['duration']*FPS)
    frames=list(range(a.start,a.end or count)) if a.all else [int(i) for i in a.frames.split(',')]
    a.out.mkdir(parents=True,exist_ok=True)
    rig,cam,scene=look.scene_setup(a.width,a.height,a.samples)
    cam.name='V7 single continuous physical camera, fixed 50mm'
    scene.frame_start,scene.frame_end=0,count-1
    root=rig['root'];root.rotation_mode='QUATERNION'
    bake_frames=sorted({frame+offset for frame in frames for offset in (-1,0,1)})
    for i in bake_frames:
        state=motion.apply_motion(i/FPS,rig)
        camera_pose(i/FPS,state,cam,metadata['duration'])
        previous.key_transform(root,i);previous.key_transform(cam,i)
        cam.data.keyframe_insert('dof.focus_distance',frame=i)
        if i%60==0:print('V7_BAKE',i,flush=True)
    previous.linear_keys(root);previous.linear_keys(cam)
    for obj in root.children:
        if hasattr(obj,'cycles'):obj.cycles.use_deform_motion=False
    scene.render.use_motion_blur=True
    scene.render.motion_blur_shutter=.30
    report={'version':'v7-pilot','frames':count,'fps':FPS,'duration':metadata['duration'],
            'width':a.width,'height':a.height,'cuts':[], 'camera_count':1,'lens_mm':50,
            'camera_method':'Continuous physical dolly, same azimuth; fixed lens and focus on actual tip/cloth.',
            'contact_time':5.0,'opening':[5.38,5.65], 'release_height_m':.82,
            'asset_status':'Existing LP reconstruction, not approved identity master.',
            'backend':scene.get('render_backend'),'samples':a.samples}
    (a.out/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for i in frames:
        dest=a.out/f'frame-{i:04}.png'
        if a.resume and dest.exists():continue
        scene.frame_set(i)
        state=motion.apply_motion(i/FPS,rig)
        camera_pose(i/FPS,state,cam,metadata['duration'])
        bpy.context.view_layer.update()
        scene.render.filepath=str(dest)
        bpy.ops.render.render(write_still=True)
        print('V7_FRAME',i,flush=True)

if __name__=='__main__':main()
