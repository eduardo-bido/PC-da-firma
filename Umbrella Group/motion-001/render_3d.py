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
    floor = mat("Charcoal studio floor", (.005, .005, .007), .86)
    wall = mat("Charcoal studio wall", (.0028, .0028, .004), .96)
    studio_corner(floor, wall)
    world = bpy.data.worlds.new("Soft graphite environment")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.04, .04, .05, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .50
    bpy.context.scene.world = world
    light("Long soft studio key", (-2.3, -2.0, 4.0), 480, 3.5, (0, 0, 1.0))
    light("Violet side bounce", (2.7, 1.1, 2.6), 210, 2.3, (0, 0, 1.0), (.82, .75, 1))
    light("Ferrule contact rake", (0.8, -1.6, .6), 72, 1.1, (0, 0, 0))
    light("Soft landing pool", (0, -1.9, 2.4), 105, 2.8, (0, 0, 0))
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.name = "Vertical moving camera"
    cam.data.type = "PERSP"
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
    # Clock is intentionally stretched for cinematic tension; the collision
    # itself is at t=5.17 and the crown ferrule remains the contact pivot.
    if t < 4.0:
        p = t / 4.0
        rise = 1.90 * (1 - .42 * p - .58 * p * p) + .22
    elif t < 5.17:
        p = smooth((t - 4.0) / 1.17)
        rise = .22 * (1 - p)
    else:
        dt = t - 5.17
        rise = .022 * math.exp(-13 * dt) * math.sin(math.pi * min(dt, .26) / .26) ** 2
    if t < 5.35:
        openness = 0.0
    else:
        openness = smooth((t - 5.35) / 1.65)
    if abs(openness - rig.get("_last_open", -1.0)) > 1e-8:
        geometry.update_opening(rig, openness)
        rig["_last_open"] = openness
    time_after = max(0, t - 7.0)
    turn = math.radians(72 * (1 - math.exp(-time_after * .48)))
    swing = math.radians(22) * math.exp(-time_after * .31) * math.sin(time_after * 2.2)
    tilt = 30 * smooth(time_after / .65)
    if time_after > .65:
        rebound = time_after - .65
        tilt -= 7 * math.exp(-2.0 * rebound) * abs(math.sin(7.5 * rebound))
    lean = math.radians(tilt)
    rotation = Quaternion((1, 0, 0), math.pi) @ Quaternion((0, 0, 1), turn + swing) @ Quaternion((0, 1, 0), lean)
    crown = Vector((0, 0, 1.26))
    rig["root"].matrix_world = Matrix.Translation((0, 0, rise)) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-crown)
    # The close shot aims at the actual crown ferrule, not a cropped cutout.
    close = smooth((t - 3.65) / 1.35) * (1 - smooth((t - 5.3) / 1.35))
    wide_loc = Vector((3.2, -6.9, 2.5))
    macro_loc = Vector((.32, -.68, .21))
    title_space = .90 * smooth((t - 7.2) / 2.0)
    wide_target = Vector((0, 0, 1.45 + .55 * (1 - smooth(t / 4.0)) - title_space))
    macro_target = Vector((0, 0, .055))
    cam.location = wide_loc.lerp(macro_loc, close)
    target = wide_target.lerp(macro_target, close)
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    # An immediate, restrained push makes the fall read in the first half second.
    wide_lens = 76 + 12 * smooth(t / 1.2) + 7 * smooth((t - 5.35) / 1.7)
    cam.data.lens = wide_lens * (1 - close) + 130 * close
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
