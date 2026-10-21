"""Motion001 v6: fixed focal lengths, deliberate cuts, local Cycles rendering."""
from __future__ import annotations
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Quaternion

HERE = Path(__file__).resolve().parent
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

look = module('look_v6', 'lookdev_v6.py')
motion = module('motion_v6', 'motion_v6.py')
FPS = 24
COUNT = 360
CUTS = (0, 30, 80, 120, 164, 204, 360)
NAMES = ('fall_portrait', 'fall_floor', 'tip_macro', 'snap_open', 'printed_brand', 'hero')

def shot(t):
    f = t * FPS
    return next((i for i in range(6) if f < CUTS[i+1]), 5)

def camera_pose(t, state, cam, which=None):
    s = shot(t) if which is None else which
    roll = 0.0
    if s == 0:
        # The object traverses a stationary portrait frame immediately.
        target = Vector((-.035, 0, 2.57))
        location = target + Vector((1.16, -1.66, .12))
        lens, fstop = 70, 5.6
        roll = math.radians(-10)
        focus = state['tip_position'] + Vector((0,0,.60))
    elif s == 1:
        # Floor and shadow establish the coming collision. Tilt is small and
        # motivated by the falling object; neither lens nor distance zooms.
        p = motion.clamp((t - 1.25) / (80/24 - 1.25))
        target = Vector((0, 0, 1.40 - .53*p))
        location = Vector((1.72, -2.46, 1.63))
        lens, fstop = 66, 7.1
        focus = state['tip_position'] + Vector((0,0,.52))
    elif s == 2:
        # Fixed macro camera sees the tip approach a visible landing plane.
        target = Vector((0, 0, .080))
        location = Vector((.255, -.365, .125))
        lens, fstop = 86, 13
        focus = state['tip_position'] + Vector((0,0,.026))
    elif s == 3:
        target = Vector((0, 0, .64))
        location = Vector((2.65, -1.88, 1.26))
        lens, fstop = 66, 8
        focus = Vector((0,0,.48))
    elif s == 4:
        # A matched product insert: the actual print, no overlay substitute.
        target = state['brand_position'] + Vector((0,0,.04))
        location = target + Vector((1.08, -.76, .25))
        lens, fstop = 86, 8
        focus = state['brand_position']
    else:
        # Quiet lateral parallax leaves the scale and floor stable under copy.
        p = motion.smooth((t - 8.5) / 6.5)
        target = Vector((0, 0, .62))
        location = Vector((2.72-.12*p, -1.92-.12*p, 1.35))
        lens, fstop = 68, 8
        focus = Vector((0,0,.48))
    cam.location = location
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = ((target-location).to_track_quat('-Z','Y')
                               @ Quaternion((0,0,1),roll))
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (location-focus).length
    return s

def key_transform(obj, frame):
    obj.keyframe_insert('location', frame=frame)
    obj.keyframe_insert('rotation_quaternion', frame=frame)

def linear_keys(obj):
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'

def prepare(rig, cam, scene, blur):
    cameras = [cam]
    for name in NAMES[1:]:
        data = cam.data.copy()
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        cameras.append(obj)
    root = rig['root']
    root.rotation_mode = 'QUATERNION'
    # Transform keyframes provide actual shutter integration for the root and
    # camera. The original linkage mesh is still evaluated explicitly per frame.
    for i in range(-1, COUNT+1):
        t = i/FPS
        state = motion.apply_motion(t, rig)
        key_transform(root, i)
        s = shot(t)
        camera_pose(t, state, cameras[s], s)
        key_transform(cameras[s], i)
        cameras[s].data.keyframe_insert('dof.focus_distance', frame=i)
        if i % 60 == 0:
            print('UMBRELLA_BAKE', i, flush=True)
    linear_keys(root)
    for obj in cameras:
        linear_keys(obj)
    for obj in root.children:
        if hasattr(obj, 'cycles'):
            obj.cycles.use_deform_motion = False
    scene.render.use_motion_blur = blur
    scene.render.motion_blur_shutter = .35
    scene.frame_start, scene.frame_end = 0, COUNT-1
    return cameras

def render(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rig, cam, scene = look.scene_setup(args.width,args.height,args.samples,args.engine)
    cameras = prepare(rig,cam,scene,not args.no_blur)
    report = motion.diagnostics(rig)
    report.update({'frames':COUNT, 'fps':FPS, 'width':args.width, 'height':args.height,
                   'engine':args.engine, 'backend':scene.get('render_backend'),
                   'cuts_frames':CUTS,'shots':NAMES,'transform_motion_blur':not args.no_blur})
    (out/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    numbers = range(args.start,args.end) if args.all else [int(n) for n in args.frames.split(',')]
    for i in numbers:
        dest = out/f'frame-{i:04d}.png'
        if args.resume and dest.is_file():
            continue
        scene.frame_set(i)
        state = motion.apply_motion(i/FPS,rig)
        s = shot(i/FPS)
        scene.camera = cameras[s]
        camera_pose(i/FPS,state,cameras[s],s)
        # Camera shutter never straddles an editorial cut.
        scene.render.use_motion_blur = not args.no_blur and i not in CUTS
        bpy.context.view_layer.update()
        scene.render.filepath = str(dest)
        bpy.ops.render.render(write_still=True)
        print('UMBRELLA_FRAME',i, NAMES[s], str(dest),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True)
    p.add_argument('--frames',default='0,20,32,65,82,104,118,124,132,148,175,200,240,320')
    p.add_argument('--all',action='store_true')
    p.add_argument('--start',type=int,default=0)
    p.add_argument('--end',type=int,default=COUNT)
    p.add_argument('--width',type=int,default=540)
    p.add_argument('--height',type=int,default=960)
    p.add_argument('--samples',type=int,default=32)
    p.add_argument('--engine',choices=('CYCLES','EEVEE'),default='CYCLES')
    p.add_argument('--no-blur',action='store_true')
    p.add_argument('--resume',action='store_true')
    render(p.parse_args(sys.argv[sys.argv.index('--')+1:]))

if __name__=='__main__':
    main()
