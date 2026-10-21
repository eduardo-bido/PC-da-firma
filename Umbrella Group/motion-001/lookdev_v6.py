"""Photographic studio look for Motion001 v6; uses the existing LP reconstruction.

No brand geometry, print pixels, or canonical source assets are replaced here.
The studio is a local, deterministic set. Cycles GPU is preferred, CPU is explicit.
"""
from pathlib import Path
import importlib.util
import math

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("umbrella_v5_materials", HERE / "render_3d_v5.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def material(name, rgb, roughness=.6, metallic=0):
    return base.mat(name, rgb, roughness, metallic)


def micro_surface(mat, scale, depth, strength, rough_lo, rough_hi):
    """Surface coordinates are metres, so the texture does not change per mesh."""
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    b = nodes.get('Principled BSDF')
    uv = nodes.new('ShaderNodeTexCoord')
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 2
    links.new(uv.outputs['Object'], tex.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = depth
    bump.inputs['Strength'].default_value = strength
    links.new(tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], b.inputs['Normal'])
    rough = nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = rough_lo
    rough.inputs['To Max'].default_value = rough_hi
    links.new(tex.outputs['Fac'], rough.inputs['Value'])
    links.new(rough.outputs['Result'], b.inputs['Roughness'])


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name + ' mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def box(name, center, scale, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def area(name, loc, target, power, width, height, color=(1, 1, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.energy = power
    obj.data.shape = 'RECTANGLE'
    obj.data.size = width
    obj.data.size_y = height
    obj.data.color = color
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


def studio():
    # Neutral graphite landing surface. No luminous material or painted contact.
    floor = material('V6 graphite painted studio floor', (.022, .021, .026), .67)
    micro_surface(floor, 420, .00012, .22, .64, .76)
    mesh('V6 floor z0', [(-16,-20,0),(16,-20,0),(16,3.2,0),(-16,3.2,0)], [(0,1,2,3)], floor)
    wall = material('V6 muted plum studio plaster', (.043, .022, .054), .89)
    micro_surface(wall, 175, .00024, .14, .85, .94)
    # A 45cm cove replaces the razor-edged plane intersection while retaining
    # a visible change in surface orientation and the floor's directional shadow.
    verts = []
    steps = 24
    for i in range(steps+1):
        a = math.pi*.5*i/steps
        y = 3.2 + .45*math.sin(a)
        z = .45*(1-math.cos(a))
        verts.extend([(-16,y,z),(16,y,z)])
    verts.extend([(-16,3.65,12),(16,3.65,12)])
    faces = [(2*i,2*i+1,2*i+3,2*i+2) for i in range(steps+1)]
    cove = mesh('V6 curved photographic backdrop', verts, faces, wall)
    for p in cove.data.polygons:
        p.use_smooth = True
    # Real shadow flags in the background-light path. They live behind the
    # umbrella and outside the hero framing; their silhouettes shape the wall.
    black = material('V6 black studio flag velvet', (.003,.003,.003), 1)
    flag = box('V6 tall background shadow flag', (-1.15,2.25,2.7), (.32,.055,5.0), black,
               (0,math.radians(-18),0))
    flag.visible_camera = False
    return floor, wall


def choose_cycles(scene, samples):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scene.cycles.denoising_prefilter = 'ACCURATE'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .025
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.sample_clamp_indirect = 3
    scene.render.use_persistent_data = True
    prefs = bpy.context.preferences.addons['cycles'].preferences
    available = {item[0] for item in prefs.get_device_types(bpy.context)}
    selected = 'CPU'
    for backend in ('OPTIX','CUDA','METAL','HIP','ONEAPI'):
        if backend not in available:
            continue
        try:
            prefs.compute_device_type = backend
            prefs.refresh_devices()
            found = [d for d in prefs.devices if d.type == backend]
            if found:
                for d in prefs.devices:
                    d.use = d.type == backend
                selected = backend
                break
        except Exception:
            continue
    scene.cycles.device = 'CPU' if selected == 'CPU' else 'GPU'
    scene['render_backend'] = selected
    print('UMBRELLA_V6_CYCLES_BACKEND', selected, flush=True)


def scene_setup(width, height, samples, engine='CYCLES'):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    mats = {
        'cloth_outer': base.lp_cloth(False),
        'cloth_inner': base.lp_cloth(True),
        'metal': material('V6 brushed dark steel', (.070,.074,.082), .26, .90),
        'grip': material('V6 moulded satin grip', (.012,.013,.016), .49),
        'seam': material('V6 violet stitched hem', (.032,.003,.075), .66),
        'thread': material('V6 violet thread', (.055,.006,.13), .64),
    }
    micro_surface(mats['grip'], 620, .000035, .18, .44, .54)
    grip = mats['grip'].node_tree.nodes.get('Principled BSDF')
    grip.inputs['IOR'].default_value = 1.46
    grip.inputs['Specular IOR Level'].default_value = .35
    rig = base.geometry.build_umbrella(mats)
    # Edge radii are finishing modifiers on existing manufactured parts. The
    # silhouette, dimensions, topology source and print remain the LP asset.
    for obj in bpy.context.scene.objects:
        if obj.parent == rig['root'] and obj.type == 'MESH' and any(
                slot.material == mats['metal'] for slot in obj.material_slots):
            bevel = obj.modifiers.new('V6 manufactured edge radius', 'BEVEL')
            bevel.width = .00035
            bevel.segments = 3
            bevel.limit_method = 'ANGLE'
            bevel.angle_limit = .6
    studio()
    world = bpy.data.worlds.new('V6 low neutral photographic ambience')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18,.19,.21,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .10
    bpy.context.scene.world = world
    lights = {
        'key': area('V6 warm neutral textile strip', (2.3,-3.1,2.6), (0,0,.6), 620,.75,2.8,(1,.94,.89)),
        'fill': area('V6 low neutral front fill', (-3,-4,2.4), (0,0,.7), 55,3,3,(.90,.94,1)),
        'rim': area('V6 subtle violet reflected edge', (-2.1,1.2,3), (0,0,.8), 85,.48,2.6,(.83,.75,1)),
        'ceiling': area('V6 overhead silk', (.2,.1,5), (0,0,0), 70,2.0,2.0,(1,.95,.90)),
        # Background-only key is behind the product; the physical flag gives
        # the shadow a coherent penumbra instead of a shader-painted gradient.
        'background': area('V6 warm wall key', (-3.3,.8,4.5), (.3,3.65,1.7), 350,.08,.08,(1,.70,.43)),
    }
    rig['_studio_lights'] = lights
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = 'V6 photographic fixed-lens camera'
    cam.data.type = 'PERSP'
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 8
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 25
    scene.render.film_transparent = False
    if engine == 'CYCLES':
        choose_cycles(scene, samples)
    else:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.eevee.taa_render_samples = samples
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = .25
    scene.view_settings.gamma = 1
    return rig, cam, scene
