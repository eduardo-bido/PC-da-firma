"""Umbrella B1: one deterministic mesh/rig, dry woven material and local Cycles proof."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import resource
import sys
import time

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('umbrella_geometry', HERE/'geometry.py')
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


def smooth(v):
    v = min(1., max(0., v))
    return v*v*v*(v*(v*6-15)+10)


def material(name, color, roughness=.5, metallic=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = roughness
    b.inputs['Metallic'].default_value = metallic
    return m


def cloth(name, inside=False):
    """Dry woven dielectric: photographic weave, seam puckers and printed ink."""
    m=material(name,(.11,.0055,.245),.53)
    n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
    b.inputs['IOR'].default_value=1.53
    b.inputs['Specular IOR Level'].default_value=.42
    b.inputs['Sheen Weight'].default_value=.045
    b.inputs['Sheen Roughness'].default_value=.70
    b.inputs['Sheen Tint'].default_value=(.28,.17,.42,1)
    if 'Anisotropic IOR Level' in b.inputs:
        b.inputs['Anisotropic IOR Level'].default_value=.18
        tangent=n.new('ShaderNodeTangent');tangent.direction_type='UV_MAP';tangent.uv_map='FabricRest'
        l.new(tangent.outputs['Tangent'],b.inputs['Tangent'])
    uv=n.new('ShaderNodeUVMap');uv.uv_map='GoreAtlas'
    fabric_uv=n.new('ShaderNodeUVMap');fabric_uv.uv_map='FabricRest'
    scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1/.3,1/.3,1)
    l.new(fabric_uv.outputs['UV'],scale.inputs[0])
    def photo(filename, noncolor=False):
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(HERE/'assets/cloth'/filename))
        tex.extension='REPEAT'
        if noncolor:tex.image.colorspace_settings.name='Non-Color'
        l.new(scale.outputs[0],tex.inputs['Vector']);return tex
    def math_node(operation,a,c=None):
        node=n.new('ShaderNodeMath');node.operation=operation
        for index,value in enumerate([a,c]):
            if value is None:continue
            if isinstance(value,(float,int)):node.inputs[index].default_value=value
            else:l.new(value,node.inputs[index])
        return node.outputs[0]
    diffuse=photo('terlenka_diff_1k.png')
    gray=n.new('ShaderNodeRGBToBW');l.new(diffuse.outputs['Color'],gray.inputs[0])
    dye=n.new('ShaderNodeMixRGB');dye.blend_type='MULTIPLY';dye.inputs[0].default_value=1
    l.new(gray.outputs[0],dye.inputs[1])
    dye.inputs[2].default_value=(.043,.0025,.086,1) if inside else (.11,.0055,.245,1)
    rough_tex=photo('terlenka_rough_1k.png',True)
    rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.60374;rough.inputs['From Max'].default_value=.72441;rough.clamp=True
    rough.inputs['To Min'].default_value=.43;rough.inputs['To Max'].default_value=.64
    l.new(rough_tex.outputs['Color'],rough.inputs['Value'])
    normal_tex=photo('terlenka_nor_gl_1k.png',True)
    normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.20;normal.uv_map='FabricRest'
    l.new(normal_tex.outputs['Color'],normal.inputs['Color'])
    # Resolved warp/weft at approximately 0.32/0.34 mm pitch. Fine photographic
    # normal variation is retained beneath an analytic interlaced thread bump.
    split=n.new('ShaderNodeSeparateXYZ');l.new(fabric_uv.outputs['UV'],split.inputs[0])
    px=math_node('MULTIPLY',split.outputs['X'],math.tau/.00032)
    py=math_node('MULTIPLY',split.outputs['Y'],math.tau/.00034)
    wx=math_node('MULTIPLY',math_node('ADD',math_node('COSINE',px),1),.5)
    wy=math_node('MULTIPLY',math_node('ADD',math_node('COSINE',py),1),.5)
    over=math_node('MULTIPLY',math_node('COSINE',math_node('MULTIPLY',px,.5)),math_node('COSINE',math_node('MULTIPLY',py,.5)))
    over=math_node('ADD',math_node('MULTIPLY',over,.42),.5)
    weave_height=math_node('ADD',math_node('MULTIPLY',wx,over),math_node('MULTIPLY',wy,math_node('SUBTRACT',1,over)))
    # Weak directional yarn tone, not random grain or enlarged weave.
    yarn_tone=math_node('ADD',.94,math_node('MULTIPLY',weave_height,.08))
    yarn_dye=n.new('ShaderNodeMixRGB');yarn_dye.blend_type='MULTIPLY';yarn_dye.inputs[0].default_value=1
    l.new(dye.outputs[0],yarn_dye.inputs[1]);l.new(yarn_tone,yarn_dye.inputs[2])
    weave=n.new('ShaderNodeBump');weave.inputs['Distance'].default_value=.000035;weave.inputs['Strength'].default_value=.55
    l.new(weave_height,weave.inputs['Height']);l.new(normal.outputs['Normal'],weave.inputs['Normal'])
    # Fine puckering follows each gore edge; broad wrinkles remain very shallow.
    separate=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],separate.inputs[0])
    local=math_node('FRACT',math_node('MULTIPLY',separate.outputs['X'],8))
    edge=math_node('POWER',math_node('MULTIPLY',math_node('ABSOLUTE',math_node('SUBTRACT',local,.5)),2),12)
    warp=n.new('ShaderNodeTexNoise');warp.inputs['Scale'].default_value=4;warp.inputs['Detail'].default_value=2
    l.new(uv.outputs['UV'],warp.inputs['Vector'])
    wrinkle_phase=math_node('ADD',math_node('MULTIPLY',local,math.tau*3),math_node('MULTIPLY',warp.outputs['Fac'],2.0))
    broad=math_node('MULTIPLY',math_node('ADD',math_node('SINE',wrinkle_phase),1),.0)
    pucker_phase=math_node('ADD',math_node('MULTIPLY',separate.outputs['Y'],math.tau*65),math_node('MULTIPLY',warp.outputs['Fac'],3))
    small=math_node('MULTIPLY',math_node('ADD',math_node('SINE',pucker_phase),1),edge)
    height=math_node('ADD',broad,small)
    pucker=n.new('ShaderNodeBump');pucker.inputs['Strength'].default_value=.18;pucker.inputs['Distance'].default_value=.00010
    l.new(height,pucker.inputs['Height']);l.new(weave.outputs['Normal'],pucker.inputs['Normal'])
    if inside:
        l.new(yarn_dye.outputs[0],b.inputs['Base Color']);l.new(rough.outputs[0],b.inputs['Roughness'])
        l.new(pucker.outputs['Normal'],b.inputs['Normal'])
    else:
        atlas=n.new('ShaderNodeTexImage');atlas.image=bpy.data.images.load(str(HERE/'umbrella-print-atlas.png'))
        atlas.interpolation='Linear';atlas.extension='CLIP'
        flip=n.new('ShaderNodeVectorMath');flip.operation='MULTIPLY';flip.inputs[1].default_value=(1,-1,1)
        offset=n.new('ShaderNodeVectorMath');offset.operation='ADD';offset.inputs[1].default_value=(0,1,0)
        l.new(uv.outputs['UV'],flip.inputs[0]);l.new(flip.outputs[0],offset.inputs[0])
        ink_scale=n.new('ShaderNodeVectorMath');ink_scale.operation='MULTIPLY';ink_scale.inputs[1].default_value=(1.45,1.45,1)
        ink_center=n.new('ShaderNodeVectorMath');ink_center.operation='ADD';ink_center.inputs[1].default_value=(-.028125,-.1035,0)
        l.new(offset.outputs[0],ink_scale.inputs[0]);l.new(ink_scale.outputs[0],ink_center.inputs[0]);l.new(ink_center.outputs[0],atlas.inputs['Vector'])
        paint=n.new('ShaderNodeMixRGB');paint.blend_type='MIX'
        l.new(atlas.outputs['Alpha'],paint.inputs[0]);l.new(yarn_dye.outputs[0],paint.inputs[1]);paint.inputs[2].default_value=(.86,.86,.89,1)
        l.new(paint.outputs[0],b.inputs['Base Color'])
        ink_rough=n.new('ShaderNodeMixRGB');ink_rough.blend_type='MIX'
        l.new(atlas.outputs['Alpha'],ink_rough.inputs[0]);l.new(rough.outputs[0],ink_rough.inputs[1]);ink_rough.inputs[2].default_value=(.62,.62,.62,1)
        l.new(ink_rough.outputs[0],b.inputs['Roughness'])
        ink=n.new('ShaderNodeBump');ink.inputs['Distance'].default_value=.00002;ink.inputs['Strength'].default_value=.5
        l.new(atlas.outputs['Alpha'],ink.inputs['Height']);l.new(pucker.outputs['Normal'],ink.inputs['Normal']);l.new(ink.outputs['Normal'],b.inputs['Normal'])
    return m


def area(name,loc,power,size,color=(1,1,1),target=(0,0,.85),size_y=None):
    bpy.ops.object.light_add(type='AREA',location=loc)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color
    o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=size_y or size
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o


def setup(args):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mats={
      'cloth_outer':cloth('Umbrella_dry_woven_violet_print'),
      'cloth_inner':cloth('Umbrella_dry_inner_weave',True),
      'metal':material('Dark_brushed_steel',(.065,.071,.084),.29,.87),
      'grip':material('Satin_black_grip',(.012,.014,.018),.39,.03),
      'seam':material('Fine_violet_stitched_hem',(.032,.003,.075),.66),
      'thread':material('Violet_polyester_thread',(.055,.006,.13),.64),
      'print':material('White_textile_ink',(.86,.86,.89),.55),
    }
    rig=geometry.build_umbrella(mats)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=args.samples
    scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
    scene.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
    scene.cycles.denoising_prefilter='ACCURATE'
    scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
    scene.render.resolution_x=args.width;scene.render.resolution_y=args.height
    scene.render.resolution_percentage=100;scene.render.film_transparent=False
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.fps=args.fps;scene.render.use_persistent_data=True
    world=bpy.data.worlds.new('Neutral_graphite_studio');scene.world=world;world.use_nodes=True
    bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.021,.020,.026,1)
    bg.inputs['Strength'].default_value=.18
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except TypeError:pass
    scene.view_settings.exposure=0
    # Broad low-energy fill opens the dark gores without a white spotlight.
    area('Fixed_raking_textile_strip',(-2.4,-2.0,1.75),140,.50,(1,.98,.97),target=(0,0,1.05),size_y=2.0)
    area('Fixed_neutral_fill',(4,1,3.5),22,5,(.92,.95,1))
    area('V7_balanced_soft_front',(2,-4,2.3),85,2.5,(1,1,1),target=(0,0,.95),size_y=2.5)
    area('Fixed_soft_edge',(-2,3.5,4.2),75,2.5,(1,1,1),size_y=.16)
    hardware=area('Fixed_lower_hardware_fill',(1.5,-2.2,.75),180,.65,(.92,.95,1),target=(0,0,.35),size_y=1.2)
    receivers=bpy.data.collections.new('Hardware_light_receivers_only')
    for obj in scene.objects:
        if obj.type in ['MESH','CURVE'] and any(slot.material and slot.material.name.startswith(('Dark_brushed_steel','Satin_black_grip')) for slot in obj.material_slots):
            receivers.objects.link(obj)
    hardware.light_linking.receiver_collection=receivers
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Cinema_85mm'
    cam.data.lens=85;cam.data.sensor_width=36;cam.data.shift_x=-.10
    cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=8
    scene.camera=cam
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    gpu=[d for d in prefs.devices if d.type=='METAL']
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU' if gpu else 'CPU'
    if not gpu:raise RuntimeError('Metal unavailable for this B1 run; no silent CPU fallback')
    return rig,cam,scene,{'devices':[{'name':d.name,'type':d.type,'use':bool(d.use)} for d in prefs.devices]}


def state(pose,t=0):
    if pose=='macro':return {'yaw':0,'open':1,'tilt':-6,'crown':0,'macro':1}
    if pose=='open':return {'yaw':0,'open':1,'tilt':-6,'crown':0}
    if pose=='rear':return {'yaw':150,'open':1,'tilt':-6,'crown':0}
    if pose=='half':return {'yaw':0,'open':.5,'tilt':-6,'crown':0}
    if pose=='closed':return {'yaw':0,'open':0,'tilt':-6,'crown':0}
    if pose=='crown':return {'yaw':150,'open':1,'tilt':42,'crown':1}
    if pose=='spin':return {'yaw':150*smooth(t),'open':1,'tilt':-6,'crown':0,'macro':1-smooth(t/.48)}
    if pose=='crown_motion':
        # Continuous crown gesture: same entry, peak and exit without baked holds.
        q=math.sin(math.pi*min(1,max(0,t)))**2
        return {'yaw':150,'open':1,'tilt':-6+48*q,'crown':q}
    if pose=='mechanism':
        if t<.42:u=1-smooth(t/.42)
        elif t<.58:u=0
        else:u=smooth((t-.58)/.42)
        return {'yaw':150+210*smooth(t),'open':u,'tilt':-6*(1-smooth(t)),'crown':0}
    raise ValueError(pose)


def apply(rig,cam,s):
    geometry.update_opening(rig,s['open'])
    az=math.radians(-42)
    direction=Vector((math.cos(az),math.sin(az),0))
    axis=Vector((0,0,1)).cross(direction).normalized()
    q=Quaternion(axis,math.radians(s['tilt'])) @ Quaternion((0,0,1),math.radians(s['yaw']))
    pivot=Vector((0,0,.65))
    rig['root'].matrix_world=Matrix.Translation(pivot) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    crown_q=s['crown']
    target=Vector((0,0,.69)).lerp(rig['root'].matrix_world @ Vector((0,0,1.20)),crown_q)
    elevation=math.radians(8+20*crown_q)
    distance=6.9+3*crown_q
    macro=s.get('macro',0)
    if macro:
        # Moderate establishing view, with the whole physical object in frame.
        target=target.lerp(Vector((0,0,.76)),macro)
        elevation=elevation*(1-macro)+math.radians(32)*macro
        distance=distance*(1-macro)+4.8*macro
    cam.data.lens=85-19*macro
    cam.data.shift_x=-.10+.02*macro
    cam.location=target+Vector((direction.x*math.cos(elevation),direction.y*math.cos(elevation),math.sin(elevation)))*distance
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.dof.focus_distance=(cam.location-target).length
    cam.data.dof.aperture_fstop=8+8*macro
    bpy.context.view_layer.update()


def audit_rig(rig):
    import struct
    def mesh_hash():
        return hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in rig['canopy'].data.vertices)).hexdigest()
    geometry.update_opening(rig,1)
    initial_hash=mesh_hash()
    uv_initial={layer.name:[tuple(x.uv) for x in layer.data] for layer in rig['canopy'].data.uv_layers}
    rows=[]
    for u in [1,.75,.5,.25,0,.25,.5,.75,1]:
        geometry.update_opening(rig,u)
        rig['canopy'].data.update()
        rows.append({'open':u,'surface_area':sum(p.area for p in rig['canopy'].data.polygons)})
    assert mesh_hash()==initial_hash,'Reopened mesh differs from initial open mesh'
    assert {layer.name:[tuple(x.uv) for x in layer.data] for layer in rig['canopy'].data.uv_layers}==uv_initial,'UV changed during cycle'
    assert len(rig['ribs'])==len(rig['tips'])==len(rig['stretchers'])==8
    return {'states':rows,'reopened_mesh_identical':True,'uv_invariant':True,'uv_layers':list(uv_initial),'thread_segments':len(rig.get('stitch_specs',[])),'ribs':8,'tips':8,'stretchers':8,
        'minimum_area_ratio':min(x['surface_area'] for x in rows)/rows[0]['surface_area'],
        'maximum_area_ratio':max(x['surface_area'] for x in rows)/rows[0]['surface_area']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--pose',default='open',choices=['audit','macro','open','rear','half','closed','crown','spin','crown_motion','mechanism'])
    parser.add_argument('--frames',type=int,default=1)
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--stop',type=int,default=None)
    parser.add_argument('--step',type=int,default=1)
    parser.add_argument('--width',type=int,default=960)
    parser.add_argument('--height',type=int,default=540)
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--fps',type=int,default=24)
    parser.add_argument('--save-blend',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();rig,cam,scene,backend=setup(args)
    mechanical_audit=audit_rig(rig)
    print('UMBRELLA_MECHANICAL_AUDIT '+json.dumps(mechanical_audit),flush=True)
    rows=[]
    count=args.frames;stop=args.stop if args.stop is not None else count
    if args.step<1:raise ValueError('Step must be positive')
    for i in range(args.start,min(stop,count),args.step):
        frame_start=time.perf_counter()
        s=state(['open','half','closed','crown','macro'][i]) if args.pose=='audit' else state(args.pose,i/(count-1) if count>1 else 0)
        apply(rig,cam,s)
        filename=f'{args.pose}-{i:04d}.png'
        scene.render.filepath=str(out/filename)
        bpy.ops.render.render(write_still=True)
        rows.append({'frame':i,'file':filename,'state':s,'seconds':round(time.perf_counter()-frame_start,3)})
        (out/(args.pose+'-progress.json')).write_text(json.dumps(rows,indent=2)+'\n')
        print('UMBRELLA_FRAME '+json.dumps(rows[-1]),flush=True)
    if args.save_blend:
        apply(rig,cam,state('open'))
        for image in bpy.data.images:
            if image.source=='FILE':image.pack()
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'umbrella-b1.blend'))
    report={'phase':'B1 experimental reconstructed scene, not production approved',
        'blender':bpy.app.version_string,'backend':backend,'dry_cloth':True,'droplets':False,'material_revision':7,'shape_revision':7,'motion_state_timing_unchanged':True,'macro_reframed':True,
        'drops_omission_authorized_by_user':True,'canonical_gores':8,
        'cloth_pbr_source':'Poly Haven Terlenka CC0 1K photographic polyester weave, tinted violet; source and hashes in assets/cloth/MANIFEST.json',
        'frames':rows,'mechanical_audit':mechanical_audit,'total_seconds':round(time.perf_counter()-started,3),
        'resolution':[args.width,args.height],'samples':args.samples,
        'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/(args.pose+'-report.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('UMBRELLA_REPORT '+json.dumps(report),flush=True)


if __name__=='__main__':main()

