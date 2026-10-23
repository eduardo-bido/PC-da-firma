"""Approved V8: visible initial fall, slow-motion approach, in-world wall branding.

Reuses the existing umbrella/print and V7.1 opening, camera and settle after 5 s.
The wall graphic samples the exact alpha region of the source print atlas.
"""
from pathlib import Path
import json
import math
import sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_3d_v7 as base

def fall_clock(t):
    p=base.motion._PHYSICAL_HIT
    times=(0,.35,1.2,3.4,5.0)
    values=(0,.50*p,.70*p,.95*p,p)
    slopes=(1.6*p,.36*p,.15*p,.035*p,.018*p)
    t=min(5,max(0,t));i=next((i for i in range(4) if t<=times[i+1]),3)
    d=times[i+1]-times[i];u=(t-times[i])/d
    return ((2*u**3-3*u*u+1)*values[i]+(u**3-2*u*u+u)*d*slopes[i]
            +(-2*u**3+3*u*u)*values[i+1]+(u**3-u*u)*d*slopes[i+1])

original_camera=base.camera_pose
def camera_pose(t,state,cam,duration):
    original_camera(t,state,cam,duration)
    if t<=1.2:
        # Hold the initial framing briefly: a real screen-space drop is visible
        # before the camera catches the tip. Same dolly/lens as approved V7.
        u=base.smooth5(t/5)
        moving=state['tip_position'].z+.19*(1-u)+.027*u
        held=base.motion.FALL_HEIGHT+.19
        follow=base.smooth5((t-.32)/.88)
        offset=held*(1-follow)+moving*follow-moving
        cam.location.z+=offset
        target=Vector((0,0,moving+offset))
        cam.rotation_quaternion=(target-cam.location).to_track_quat('-Z','Y')
        cam.data.dof.focus_distance=(cam.location-(state['tip_position']+Vector((0,0,.015)))).length

def wall_hit(cam,scene,u,v):
    cam.data.sensor_fit='HORIZONTAL'
    direction=cam.rotation_quaternion @ Vector(((u-.5)*.036/.05,(v-.5)*.064/.05,-1))
    return cam.location+direction*((3.647-cam.location.y)/direction.y)

def wall_wordmark(scene,cam):
    # Place by the initial composition, then leave fixed in world space.
    center=wall_hit(cam,scene,.82,.88)
    width=1.3;height=width*57/309
    x,y,z=center
    mesh=bpy.data.meshes.new('Umbrella source-art wall application mesh')
    mesh.from_pydata([(x-width/2,y,z-height/2),(x+width/2,y,z-height/2),
                     (x+width/2,y,z+height/2),(x-width/2,y,z+height/2)],[],[(0,1,2,3)])
    mesh.update()
    uv=mesh.uv_layers.new(name='SourceWordmark')
    for loop in mesh.loops:
        uv.data[loop.index].uv=((0,0),(1,0),(1,1),(0,1))[loop.vertex_index]
    obj=bpy.data.objects.new('Umbrella matte wall mark — exact existing print artwork',mesh)
    scene.collection.objects.link(obj)
    mat=bpy.data.materials.new('Muted warm-lilac matte wall ink');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader')
    clear=n.new('ShaderNodeBsdfTransparent');ink=n.new('ShaderNodeBsdfPrincipled')
    ink.inputs['Base Color'].default_value=(.022,.016,.029,1)
    ink.inputs['Roughness'].default_value=.92
    ink.inputs['Specular IOR Level'].default_value=.15
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(HERE/'source/umbrella-print-atlas.png'))
    tex.extension='CLIP';tex.interpolation='Linear'
    coord=n.new('ShaderNodeUVMap');coord.uv_map='SourceWordmark'
    scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(309/4096,57/1024,1)
    shift=n.new('ShaderNodeVectorMath');shift.operation='ADD';shift.inputs[1].default_value=(102/4096,1-782/1024,0)
    l.new(coord.outputs['UV'],scale.inputs[0]);l.new(scale.outputs[0],shift.inputs[0])
    l.new(shift.outputs[0],tex.inputs['Vector']);l.new(tex.outputs['Alpha'],mix.inputs[0])
    l.new(clear.outputs[0],mix.inputs[1]);l.new(ink.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    obj.data.materials.append(mat)
    bpy.data.collections['V6 backdrop light receivers'].objects.link(obj)
    # Applied ink sits 3 mm in front of the wall; it remains opaque on glyphs.
    return obj

original_setup=base.look.scene_setup
def scene_setup(width,height,samples):
    rig,cam,scene=original_setup(width,height,samples)
    state=base.motion.apply_motion(0,rig);camera_pose(0,state,cam,481/24)
    bpy.context.view_layer.update()
    obj=wall_wordmark(scene,cam)
    # Fresh scene synchronization per render prevents reusing the GPU state
    # that was associated with isolated lighting flashes in the previous run.
    scene.render.use_persistent_data=False
    scene.cycles.seed=0
    layout={}
    for t in (0,.35,1.2,3.4,5,6,14,20):
        state=base.motion.apply_motion(t,rig);camera_pose(t,state,cam,481/24)
        bpy.context.view_layer.update()
        corners=[world_to_camera_view(scene,cam,obj.matrix_world @ v.co) for v in obj.data.vertices]
        tip=world_to_camera_view(scene,cam,state['tip_position'])
        layout[str(t)]={'mark_box_uv':[min(p.x for p in corners),min(p.y for p in corners),
            max(p.x for p in corners),max(p.y for p in corners)],'tip_uv':list(tip)}
    (HERE/'v8').mkdir(exist_ok=True)
    (HERE/'v8/layout-report.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
    return rig,cam,scene

base.motion.fall_clock=fall_clock
base.camera_pose=camera_pose
base.look.scene_setup=scene_setup

if __name__=='__main__':
    base.main()
    argv=sys.argv[sys.argv.index('--')+1:]
    out=Path(argv[argv.index('--out')+1]).resolve()
    report=json.loads((out/'render-report.json').read_text(encoding='utf-8'))
    report.update(version='v8',wall_mark='Exact source print atlas alpha, physical matte wall ink, no screen overlay',
                  initial_fall='0.35 s visible descent before tracking, then continuous slow-motion approach',
                  persistent_data=False,unchanged='Umbrella, lens, opening, impact time, settling, narration and captions')
    (out/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
