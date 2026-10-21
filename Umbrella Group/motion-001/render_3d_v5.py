"""Vertical 3D previsualization using the Umbrella LP reconstruction geometry."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
spec = importlib.util.spec_from_file_location("umbrella_geometry", SOURCE / "geometry.py")
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


def clamp(x):
    return max(0.0, min(1.0, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def mat(name, rgb, roughness=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metal
    return m


def lp_cloth(inside):
    """Run the LP source material function with its verified local texture maps."""
    tree = ast.parse((SOURCE / "scene.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cloth")
    scope = {"bpy": bpy, "math": math, "HERE": SOURCE, "material": mat}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE / "scene.py"), "exec"), scope)
    material = scope["cloth"]("Umbrella LP cloth / inner" if inside else "Umbrella LP cloth / printed outer", inside=inside)
    if not inside:
        shot_atlas = SOURCE / "umbrella-print-atlas-inverted-shot.png"
        if not shot_atlas.is_file():
            raise FileNotFoundError(f"Build the shot print first: python motion-001/make_shot_atlas.py ({shot_atlas})")
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image and node.image.filepath.endswith("umbrella-print-atlas.png"):
                node.image = bpy.data.images.load(str(shot_atlas))
                break
        else:
            raise RuntimeError("The LP cloth no longer exposes its print atlas")
    return material


def fabric(outer):
    m = mat("Original violet cloth / temporary procedural texture", (0.11, 0.0055, 0.245), .56)
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Sheen Weight"].default_value = .06
    bsdf.inputs["Sheen Roughness"].default_value = .70
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 180
    noise.inputs["Detail"].default_value = 2
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .12
    bump.inputs["Distance"].default_value = .0002
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if outer:
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = "GoreAtlas"
        flip = nodes.new("ShaderNodeVectorMath")
        flip.operation = "MULTIPLY"
        flip.inputs[1].default_value = (1, -1, 1)
        add = nodes.new("ShaderNodeVectorMath")
        add.operation = "ADD"
        add.inputs[1].default_value = (0, 1, 0)
        scale = nodes.new("ShaderNodeVectorMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = (1.45, 1.45, 1)
        shift = nodes.new("ShaderNodeVectorMath")
        shift.operation = "ADD"
        shift.inputs[1].default_value = (-.028125, -.1035, 0)
        atlas = nodes.new("ShaderNodeTexImage")
        atlas.image = bpy.data.images.load(str(SOURCE / "umbrella-print-atlas.png"))
        atlas.extension = "CLIP"
        blend = nodes.new("ShaderNodeMixRGB")
        blend.blend_type = "MIX"
        blend.inputs[1].default_value = (.11, .0055, .245, 1)
        blend.inputs[2].default_value = (.86, .86, .89, 1)
        links.new(uv.outputs["UV"], flip.inputs[0])
        links.new(flip.outputs[0], add.inputs[0])
        links.new(add.outputs[0], scale.inputs[0])
        links.new(scale.outputs[0], shift.inputs[0])
        links.new(shift.outputs[0], atlas.inputs["Vector"])
        links.new(atlas.outputs["Alpha"], blend.inputs[0])
        links.new(blend.outputs[0], bsdf.inputs["Base Color"])
    return m


def light(name, location, energy, size, target, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.energy = energy
    obj.data.shape = "DISK"
    obj.data.size = size
    obj.data.color = color
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def spot(name, location, energy, size, target, color):
    bpy.ops.object.light_add(type="SPOT", location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.energy = energy
    obj.data.spot_size = size
    obj.data.spot_blend = .62
    obj.data.color = color
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def graphite_floor():
    """Subtle micro-roughness: a matte studio surface, not concrete grain."""
    floor = mat("Microtextured graphite studio floor", (.0022, .0018, .0035), .86)
    nodes, links = floor.node_tree.nodes, floor.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    coords = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 240
    noise.inputs["Detail"].default_value = 2
    links.new(coords.outputs["Object"], noise.inputs["Vector"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = .22
    rough.inputs["From Max"].default_value = .78
    rough.inputs["To Min"].default_value = .82
    rough.inputs["To Max"].default_value = .92
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    return floor


def studio_corner(floor_material, wall_material):
    # A quiet, physically legible floor-wall junction anchors the contact.
    parts = (
        ("Matte graphite floor", [(-24, -24, -.012), (24, -24, -.012),
                                  (24, 3.8, -.012), (-24, 3.8, -.012)], floor_material),
        ("Soft dark studio wall", [(-24, 3.8, -.012), (24, 3.8, -.012),
                                   (24, 3.8, 20), (-24, 3.8, 20)], wall_material),
    )
    for name, vertices, material in parts:
        mesh = bpy.data.meshes.new(name + " mesh")
        mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)


def scene_setup(width, height, samples):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    materials = {
        "cloth_outer": lp_cloth(False),
        "cloth_inner": lp_cloth(True),
        "metal": mat("Dark brushed steel", (.065, .071, .084), .29, .87),
        "grip": mat("Satin black grip", (.012, .014, .018), .39),
        "seam": mat("Violet stitched hem", (.032, .003, .075), .66),
        "thread": mat("Violet polyester thread", (.055, .006, .13), .64),
    }
    rig = geometry.build_umbrella(materials)
    floor = graphite_floor()
    wall = mat("Charcoal painted studio wall", (.015, .011, .021), .96)
    studio_corner(floor, wall)
    world = bpy.data.worlds.new("Soft graphite environment")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.045, .041, .052, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .42
    bpy.context.scene.world = world
    rig["_lights"] = {
        "key": light("Long soft studio key", (-2.3, -2.0, 4.0), 320, 3.5, (0, 0, 1.0)),
        "side": light("Brand-violet side bounce", (2.7, 1.1, 2.6), 130, 2.3, (0, 0, 1.0), (.55, .26, 1)),
        "ferrule": light("Ferrule contact rake", (0.8, -1.6, .6), 110, 1.1, (0, 0, 0)),
        "pool": light("Soft landing pool", (0, -1.9, 2.4), 30, 2.8, (0, 0, 0)),
        "edge": light("Upper violet rim strip", (-1.8, 0.7, 3.5), 70, 1.15, (0, 0, 1.0), (.78, .48, 1)),
        "wallwash": spot("Violet studio spot", (1.6, -1.8, 3.4), 600, .72, (-.15, 3.8, 1.8), (.53, .22, 1)),
        "warm": light("Warm studio bounce", (-2.5, 1.4, 2.5), 85, 2.0, (-1.1, 3.8, 1.2), (1.0, .49, .27)),
        "backspot": spot("Gel-free warm studio spot", (-2.1, -1.8, 3.8), 2100, .70, (-3.35, 3.8, 1.65), (1.0, .51, .35)),
    }
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = "Vertical moving camera"
    cam.data.type = "PERSP"
    cam.data.dof.use_dof = True
    bpy.context.scene.camera = cam
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 25
    scene.render.use_file_extension = True
    scene.eevee.taa_render_samples = samples
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    return rig, cam, scene


def pose(t, rig, cam):
    # The long fall accelerates; only its last metre is stretched for tension.
    if t < 3.65:
        p = t / 3.65
        rise = 2.30 * (1 - .58 * p - .42 * p * p) + .18
    elif t < 4.90:
        p = smooth((t - 3.65) / 1.25)
        rise = .18 * (1 - p)
    else:
        dt = t - 4.90
        rise = .045 * math.exp(-14 * dt) * math.sin(math.pi * min(dt, .22) / .22) ** 2
    if t < 5.08:
        openness = 0.0
    elif t < 5.58:
        p = clamp((t - 5.08) / .50)
        openness = 1 - (1 - p) ** 4
    elif t < 5.82:
        dt = t - 5.58
        openness = 1 - .045 * math.exp(-8 * dt) * abs(math.sin(19 * dt))
    else:
        openness = 1.0
    if abs(openness - rig.get("_last_open", -1.0)) > 1e-8:
        geometry.update_opening(rig, openness)
        rig["_last_open"] = openness
    time_after = max(0, t - 5.78)
    turn = math.radians(90 * (1 - math.exp(-time_after * .65)))
    swing = math.radians(30) * math.exp(-time_after * .42) * math.sin(time_after * 2.8)
    tilt = 29 * smooth(time_after / .37)
    if time_after > .37:
        rebound = time_after - .37
        tilt = 21 + 8 * math.exp(-.65 * rebound)
        tilt -= 8 * math.exp(-1.7 * rebound) * abs(math.sin(8.8 * rebound))
    lean = math.radians(tilt)
    if time_after > 0:
        profile = rig.setdefault("_open_profile", geometry._profile(1.0, geometry.CONFIG))
        lowest = min((1.26 - z) * math.cos(lean) - r * math.sin(lean) for r, z in profile)
        rise += max(0.0, .004 - lowest)
    rotation = Quaternion((1, 0, 0), math.pi) @ Quaternion((0, 0, 1), turn + swing) @ Quaternion((0, 1, 0), lean)
    crown = Vector((0, 0, 1.26))
    rig["root"].matrix_world = Matrix.Translation((0, 0, rise)) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-crown)
    # The close shot aims at the actual crown ferrule, not a cropped cutout.
    close = smooth((t - 3.30) / 1.35) * (1 - smooth((t - 4.98) / .68))
    drift = smooth((t - 8.12) / 6.88)
    wide_loc = Vector((3.45 - .45 * smooth(t / 4) - .50 * drift,
                       -6.7 + .2 * smooth(t / 4) + .45 * drift,
                       2.45 - .12 * drift))
    macro_loc = Vector((.32, -.68, .21))
    open_reframe = .65 * smooth((t - 5.24) / .52)
    title_space = .25 * smooth((t - 8.2) / 2.0)
    wide_target = Vector((0, 0, 1.45 + .55 * (1 - smooth(t / 4.0)) - open_reframe - title_space))
    macro_target = Vector((0, 0, .055))
    cam.location = wide_loc.lerp(macro_loc, close)
    target = wide_target.lerp(macro_target, close)
    impact_jolt = .035 * math.exp(-((t - 4.95) / .075) ** 2)
    cam.location.z += impact_jolt
    if 7.16 <= t < 8.12:
        # Intentional editorial cut to the actual printed gore on the model.
        logo_target = rig["root"].matrix_world @ Vector((.405, 0, .88))
        cam.location = logo_target + Vector((.70, -1.68, .54))
        cam.location.x += .030 * (t - 7.16)
        target = logo_target
    if t < .29:
        # The film opens inside the falling cloth, then cuts to the full fall.
        descend = .55 * smooth(t / .29)
        cam.location = Vector((.23, -.47, 3.10 - descend))
        target = Vector((0, 0, 3.02 - descend))
    elif 2.12 <= t < 2.68:
        # A tactile insert changes the scale once during the long fall.
        glide = smooth((t - 2.12) / .56)
        cam.location = Vector((-.54 - .12 * glide, -1.00, 2.35 - .30 * glide))
        target = Vector((0, 0, 2.08 - .30 * glide))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    # An immediate, restrained push makes the fall read in the first half second.
    wide_lens = 98 + 3 * smooth(t / 1.2)
    cam.data.lens = 74 if 7.16 <= t < 8.12 else 90 if t < .29 else 88 if 2.12 <= t < 2.68 else wide_lens * (1 - close) + 130 * close
    focus_target = target.lerp(Vector((0, 0, .18)), close)
    cam.data.dof.focus_distance = (cam.location - focus_target).length
    cam.data.dof.aperture_fstop = 6 if 7.16 <= t < 8.12 else 3.5 if t < .29 or 2.12 <= t < 2.68 else 8 + 8 * close
    reveal = smooth((t - 4.90) / .80)
    lights = rig["_lights"]
    lights["key"].data.energy = 320 + 190 * reveal
    lights["side"].data.energy = 130 + 280 * reveal
    lights["pool"].data.energy = 30 + 10 * reveal
    lights["edge"].data.energy = 70 + 220 * reveal
    lights["edge"].location.x = -1.8 + 3.8 * smooth((t - 5.0) / 1.65)
    lights["edge"].rotation_euler = (Vector((0, 0, 1.0)) - lights["edge"].location).to_track_quat("-Z", "Y").to_euler()
    lights["wallwash"].data.energy = 600 + 800 * reveal
    lights["warm"].data.energy = 85 + 50 * reveal
    lights["ferrule"].data.energy = 110 + 500 * math.exp(-((t - 4.90) / .11) ** 2)
    bpy.context.view_layer.update()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--frames", default="0,96,124,156,200,280")
    parser.add_argument("--all", action="store_true", help="Render all 360 frames of the 15-second cut")
    parser.add_argument("--start", type=int, default=0, help="First frame for a resumable full render")
    parser.add_argument("--end", type=int, default=360, help="Exclusive last frame for a resumable full render")
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--samples", type=int, default=32)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rig, cam, scene = scene_setup(args.width, args.height, args.samples)
    numbers = range(args.start, args.end) if args.all else [int(v) for v in args.frames.split(",") if v.strip()]
    for number in numbers:
        pose(number / 24, rig, cam)
        scene.render.filepath = str(out / f"frame-{number:04d}.png")
        bpy.ops.render.render(write_still=True)
        print("UMBRELLA_FRAME", number, scene.render.filepath, flush=True)


if __name__ == "__main__":
    main()
