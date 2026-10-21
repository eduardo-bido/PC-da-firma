"""Canonical reconstruction for Umbrella B1, not a recovered brand master.

Eight gores/ribs are an explicit production choice. Units are metres, Z is the
shaft axis, root origin is (0, 0, 0). The module owns geometry only: no scene,
camera, lights, rendering, handlers, random state, or droplets.

UV: u=(gore_index+cross)/8, v=s from crown(0) to hem(1). Gore 0 is centred on
azimuth 0 (+X), so its print centre is u=0.0625. Outer/inner material slots 0/1.

The rib is a flexible, inextensible segmented strip: every centreline segment
has fixed length. The runner is solved from a fixed-length stretcher rather
than independently translated. Cloth folding is a deterministic, area-
constrained geometric approximation, not a cloth simulation or a validated
collision-free manufacturing pattern. Its topology and UV never change.
"""

import math

import bpy
from mathutils import Vector


TAU = math.tau
CONFIG = {
    "gores": 8,
    "radial_steps": 80,
    "cross_steps": 96,
    "crown_z": 1.20,
    "rib_length": 0.93,
    "rib_radius": 0.0016,
    "stretcher_length": 0.43,
    "stretcher_attach_s": 0.36,
    "stretcher_radius": 0.0025,
    "cloth_thickness": 0.00022,
    "skin_offset": 0.0020,
    "folds_per_gore": 8,
    "closed_angle": 0.015,
    "open_angle": 1.560,
    "closed_curvature": 0.010,
    "open_curvature": -1.040,
    "seam_radius": 0.00045,
    "hem_radius": 0.00055,
    "panel_chord_blend": 0.78,
    "hem_catenary_lift": 0.024,
    "hem_cutback": 0.032,
    "panel_tension_sag": 0.0070,
}


def _clamp(value):
    return max(0.0, min(1.0, float(value)))


def _profile(openness, cfg):
    """N rigid-length links approximate a flexing rib; all N lengths stay fixed."""
    a = _clamp(openness)
    angle = cfg["closed_angle"] + a * (cfg["open_angle"] - cfg["closed_angle"])
    bend = cfg["closed_curvature"] + a * (cfg["open_curvature"] - cfg["closed_curvature"])
    count = cfg["radial_steps"]
    step = cfg["rib_length"] / count
    points = [(0.0, cfg["crown_z"])]
    radius, height = points[0]
    for i in range(count):
        theta = angle + bend * (i + 0.5) / count
        radius += step * math.sin(theta)
        height -= step * math.cos(theta)
        points.append((radius, height))
    return points


def _profile_sample(profile, s):
    q = _clamp(s) * (len(profile) - 1)
    index = min(len(profile) - 2, int(q))
    f = q - index
    r0, z0 = profile[index]
    r1, z1 = profile[index + 1]
    return r0 + f * (r1 - r0), z0 + f * (z1 - z0)


def _normal_rz(profile, s):
    index = min(len(profile) - 2, int(_clamp(s) * (len(profile) - 1)))
    dr = profile[index + 1][0] - profile[index][0]
    dz = profile[index + 1][1] - profile[index][1]
    length = math.hypot(dr, dz)
    return -dz / length, dr / length


def _skin_offset(cfg, s):
    """Cover the rib by 2 mm along its outward meridional normal.

    Fade only under the crown ferrule to keep the welded crown a single point.
    The support centreline and all its fixed-length segments remain untouched.
    """
    t = min(1.0, max(0.0, s) / 0.08)
    return cfg["skin_offset"] * t * t * (3.0 - 2.0*t)


def _point(cfg, profile, s, cross, gore, amplitude, openness):
    """The positive meridional accordion stores fabric between the fixed ribs."""
    r, z = _profile_sample(profile, s)
    t = _clamp(cross)
    panel = int(gore) % cfg["gores"]
    phi = TAU * ((panel + t - 0.5) / cfg["gores"])
    # Small longitudinal variation breaks ruler-straight accordion ridges.
    # Both gore edges remain anchored and the open state remains unchanged.
    longitudinal = 0.10 * (1.0-openness) * math.sin(math.pi*t) * math.sin(TAU*s)
    # Broad gores fold first; finer packing enters smoothly only near closure.
    # Both bases vanish at gore boundaries, so edges and fixed UV remain welded.
    pack = _clamp((0.5 - openness) * 2.0)
    pack = pack*pack*pack*(pack*(pack*6.0-15.0)+10.0)
    broad = (math.sin(math.pi * 2 * t) + longitudinal) ** 2
    fine = (math.sin(math.pi * cfg["folds_per_gore"] * t) + longitudinal) ** 2
    wave = (1.0-pack)*broad + pack*fine
    nr, nz = _normal_rz(profile, s)
    fold = amplitude * wave
    r += fold * nr
    z += fold * nz
    # A cut gore spans between two supported ribs instead of following a
    # continuous circular shell. The chord produces a shallow normal break
    # at the sewn rib line, while a small residual camber keeps the fabric taut.
    scallop = math.sin(math.pi*t)**2
    half = math.pi/cfg["gores"]
    delta = (2*t-1)*half
    chord_radius = math.cos(half)/math.cos(delta)
    r *= 1-openness*openness*cfg["panel_chord_blend"]*(1-chord_radius)
    # A small transverse sag resolves tensile cloth between the supports.
    z -= cfg["panel_tension_sag"]*openness*scallop*math.sin(math.pi*s)
    # The cut hem has a catenary recess, not a sinusoidal inflatable wave.
    catenary=(math.cosh(1.5)-math.cosh(1.5*(2*t-1)))/(math.cosh(1.5)-1)
    hem_weight=s**10
    r -= cfg["hem_cutback"]*openness*catenary*hem_weight
    z += cfg["hem_catenary_lift"]*openness*catenary*hem_weight
    # Millimetre seam puckering, resolved by the denser fixed tessellation.
    near_seam = (t*math.exp(-22*t)+(1-t)*math.exp(-22*(1-t))) * 22
    pucker = 0.0040 * openness * math.sin(math.pi*s) * near_seam * math.sin(TAU*(8*s+0.12*math.sin(TAU*t)))
    r += pucker*nr
    z += pucker*nz
    # Tiny diagonal sewing-memory marks are local to stitch allowances.
    # They end within a few centimetres of a seam rather than sculpting the
    # complete open panel into a broad radial sunburst.
    edge_distance=min(t,1-t)
    seam_window=(edge_distance/.025)*math.exp(-edge_distance/.035)
    local_memory=0.0
    for index,centre in enumerate([.27+.012*math.sin(panel*1.9),.66+.016*math.cos(panel*2.3)]):
        diagonal=s-centre-.23*edge_distance
        window=math.exp(-(diagonal/.032)**2)
        local_memory+=window*math.sin(TAU*(diagonal/.018+index*.31))
    memory=.0018*openness*openness*seam_window*local_memory*math.sin(math.pi*s)
    r+=memory*nr;z+=memory*nz
    # Unstrapped cloth hangs between fixed ferrules rather than forming a ruler.
    z -= 0.025 * (1.0-openness) * scallop * s ** 4
    # External fabric skin covers the original inextensible rib centreline.
    # The area solver and UV sampling use this same displaced surface.
    skin = _skin_offset(cfg, s)
    r += skin * nr
    z += skin * nz
    # Do not sculpt broad radial furrows into the open gores. Manufacturing
    # detail is carried by supported seams, binding, tension and fibre normals.
    return r * math.cos(phi), r * math.sin(phi), z


def _distance(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _triangle_area(a, b, c):
    ax, ay, az = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    bx, by, bz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
    return 0.5 * math.sqrt((ay*bz-az*by)**2 + (az*bx-ax*bz)**2 + (ax*by-ay*bx)**2)


def _cross_length(cfg, profile, s, amplitude, openness):
    previous = _point(cfg, profile, s, 0.0, 0, amplitude, openness)
    total = 0.0
    for j in range(1, cfg["cross_steps"]+1):
        point = _point(cfg, profile, s, j/cfg["cross_steps"], 0, amplitude, openness)
        total += _distance(previous, point)
        previous = point
    return total


def _gore_grid(cfg, profile, amplitudes, openness):
    return [[_point(cfg, profile, i/cfg["radial_steps"],
                    j/cfg["cross_steps"], 0, amplitudes[i], openness)
             for j in range(cfg["cross_steps"]+1)]
            for i in range(cfg["radial_steps"]+1)]


def _gore_area(grid):
    total = 0.0
    for i in range(len(grid)-1):
        for j in range(len(grid[i])-1):
            a, b, c, d = grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1]
            total += _triangle_area(a, b, c) + _triangle_area(a, c, d)
    return total


def _fold_state(cfg, openness, target_lengths, target_area):
    """Keep total cloth area by varying pleat depth, never scaling the mesh.

    Ring-length preservation gives an initial accordion. A global fold-depth
    solve then restores the triangulated open-state pattern area. This does
    not claim every local material strain or self-contact is physically solved.
    """
    a = _clamp(openness)
    profile = _profile(a, cfg)
    if a >= 1.0 - 1e-12:
        amplitudes = [0.0] * (cfg["radial_steps"]+1)
        grid = _gore_grid(cfg, profile, amplitudes, a)
        return profile, amplitudes, grid, _gore_area(grid)
    raw = [0.0]
    for i in range(1, cfg["radial_steps"]+1):
        s = i/cfg["radial_steps"]
        lo, hi = 0.0, max(0.03, target_lengths[i])
        for _ in range(15):
            mid = (lo+hi)*0.5
            if _cross_length(cfg, profile, s, mid, a) < target_lengths[i]:
                lo = mid
            else:
                hi = mid
        raw.append((lo+hi)*0.5)
    lo, hi = 0.0, 2.0
    for _ in range(16):
        mid = (lo+hi)*0.5
        grid = _gore_grid(cfg, profile, [x*mid for x in raw], a)
        if _gore_area(grid) < target_area:
            lo = mid
        else:
            hi = mid
    amplitudes = [x*(lo+hi)*0.5 for x in raw]
    grid = _gore_grid(cfg, profile, amplitudes, a)
    return profile, amplitudes, grid, _gore_area(grid)


def _mesh(name, vertices, faces, material, parent):
    data = bpy.data.meshes.new(name+"Mesh")
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    if material is not None:
        data.materials.append(material)
    for polygon in data.polygons:
        polygon.use_smooth = True
    return obj


def _cylinder(name, radius, depth, material, parent, z=0.0, sides=16):
    vertices = [(radius*math.cos(TAU*i/sides), radius*math.sin(TAU*i/sides), h)
                for h in (-depth/2, depth/2) for i in range(sides)]
    faces = [(i, (i+1)%sides, (i+1)%sides+sides, i+sides) for i in range(sides)]
    faces += [tuple(reversed(range(sides))), tuple(range(sides, sides*2))]
    obj = _mesh(name, vertices, faces, material, parent)
    obj.location.z = z
    return obj


def _curve(name, points, radius, material, parent, cyclic=False):
    data = bpy.data.curves.new(name+"Curve", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 1
    data.resolution_u = 1
    data.use_fill_caps = not cyclic
    spline = data.splines.new("POLY")
    spline.points.add(len(points)-1)
    spline.use_cyclic_u = cyclic
    for p, co in zip(spline.points, points):
        p.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    if material is not None:
        data.materials.append(material)
    return obj


def _set_curve(obj, points):
    for point, coordinate in zip(obj.data.splines[0].points, points):
        point.co = (*coordinate, 1.0)


def _tip(name, material, parent):
    # A short capped ferrule, not an ornamental ball or a water droplet.
    return _cylinder(name, 0.0050, 0.018, material, parent, sides=12)


def _canopy_topology(cfg):
    circumference = cfg["gores"]*cfg["cross_steps"]
    # One crown and shared seam vertices: no disconnected gore cards.
    vertices = [(0.0, 0.0, cfg["crown_z"])]
    vertices += [(0.0, 0.0, 0.0)]*(cfg["radial_steps"]*circumference)
    faces, face_uv = [], []
    for j in range(circumference):
        j1 = (j+1)%circumference
        u0, u1 = j/circumference, (j+1)/circumference
        faces.append((0, 1+j, 1+j1))
        face_uv.append((((u0+u1)/2, 0.0), (u0, 1/cfg["radial_steps"]),
                        (u1, 1/cfg["radial_steps"])))
    for i in range(1, cfg["radial_steps"]):
        for j in range(circumference):
            j1 = (j+1)%circumference
            lower = 1+(i-1)*circumference
            upper = 1+i*circumference
            faces.append((lower+j, upper+j, upper+j1, lower+j1))
            u0, u1 = j/circumference, (j+1)/circumference
            v0, v1 = i/cfg["radial_steps"], (i+1)/cfg["radial_steps"]
            face_uv.append(((u0,v0),(u0,v1),(u1,v1),(u1,v0)))
    return vertices, faces, face_uv


def _surface_attachment(name, specs, faces, material, root, cfg):
    """A thin sewn textile part attached to fixed cut-pattern coordinates."""
    obj=_mesh(name,[(0,0,0)]*len(specs),faces,material,root)
    rest_profile=_profile(1,cfg)
    atlas=obj.data.uv_layers.new(name="GoreAtlas")
    fabric=obj.data.uv_layers.new(name="FabricRest")
    for polygon in obj.data.polygons:
        for loop_index in polygon.loop_indices:
            gore,cross,s,lift=specs[obj.data.loops[loop_index].vertex_index]
            radius,_=_profile_sample(rest_profile,s)
            width=2*radius*math.sin(math.pi/cfg["gores"])
            atlas.data[loop_index].uv=((gore+cross)/cfg["gores"],s)
            fabric.data[loop_index].uv=((cross-.5)*width+gore*.137,s*cfg["rib_length"]+gore*.071)
    obj.data.uv_layers.active_index=0
    return obj,specs


def _sewn_parts(materials,root,cfg):
    """Flat-felled seam allowances, folded edge binding and crown reinforcement."""
    attachments=[]
    rest=_profile(1,cfg)
    columns=[-1,-.55,0,.55,1]
    specs=[];faces=[]
    for gore in range(cfg["gores"]):
        base=len(specs)
        for index in range(cfg["radial_steps"]+1):
            s=.06+.935*index/cfg["radial_steps"]
            radius,_=_profile_sample(rest,s)
            width=2*radius*math.sin(math.pi/cfg["gores"])
            for across in columns:
                fraction=min(.18,abs(across)*.004/width)
                panel=(gore-1)%cfg["gores"] if across<0 else gore
                cross=1-fraction if across<0 else fraction
                lift=.00030+.00010*(1-abs(across))
                specs.append((panel,cross,s,lift))
        for index in range(cfg["radial_steps"]):
            for j in range(len(columns)-1):
                a=base+index*len(columns)+j
                faces.append((a,a+len(columns),a+len(columns)+1,a+1))
    attachments.append(_surface_attachment("FlatFelledSeamAllowances_8mm",specs,faces,materials["cloth_outer"],root,cfg))
    circumference=cfg["gores"]*cfg["cross_steps"]
    specs=[];faces=[]
    rows=[(1-.006/cfg["rib_length"],.00012),(1-.003/cfg["rib_length"],.0005),
          (1-.001/cfg["rib_length"],.0006),(1,.00025)]
    for s,lift in rows:
        for j in range(circumference):
            specs.append((j//cfg["cross_steps"],(j%cfg["cross_steps"])/cfg["cross_steps"],s,lift))
    for row in range(len(rows)-1):
        for j in range(circumference):
            nxt=(j+1)%circumference
            faces.append((row*circumference+j,(row+1)*circumference+j,
                          (row+1)*circumference+nxt,row*circumference+nxt))
    attachments.append(_surface_attachment("FoldedBiasHemBinding_6mm",specs,faces,materials["cloth_outer"],root,cfg))
    specs=[(0,0,0,.0004)];faces=[]
    segments=64
    for s in [.025,.052]:
        for j in range(segments):
            specs.append((j//8,(j%8)/8,s,.00045))
    for j in range(segments):
        nxt=(j+1)%segments
        faces.append((0,1+j,1+nxt))
        faces.append((1+j,1+segments+j,1+segments+nxt,1+nxt))
    attachments.append(_surface_attachment("CrownTextileReinforcement",specs,faces,materials["cloth_outer"],root,cfg))
    return attachments


def sample_surface(rig, gore, cross, s, openness=None):
    """Return a local-space Vector on the outer base surface (before thickness)."""
    cfg = rig["config"]
    a = rig["openness"] if openness is None else _clamp(openness)
    if abs(a-rig["openness"]) < 1e-12:
        profile, amplitudes = rig["_profile"], rig["_amplitudes"]
    else:
        profile, amplitudes, _, _ = _fold_state(cfg, a, rig["_target_lengths"], rig["_target_area"])
    q = _clamp(s)*cfg["radial_steps"]
    i = min(cfg["radial_steps"]-1, int(q))
    f = q-i
    amplitude = amplitudes[i]*(1-f)+amplitudes[i+1]*f
    return Vector(_point(cfg, profile, _clamp(s), cross, gore, amplitude, a))


def build_umbrella(materials):
    """Build once. Required keys: cloth_outer, cloth_inner, metal, grip, seam.

    ``print`` may be supplied but no floating label is created: the caller's
    cloth_outer shader owns the fixed single-gore UV print.
    """
    cfg = dict(CONFIG)
    root = bpy.data.objects.new("UmbrellaRoot", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.15
    bpy.context.collection.objects.link(root)
    root["reconstruction"] = "8 gores/ribs are a production choice; not recovered from raster references"
    root["pivot_contract"] = "origin(0,0,0); shaft Z; caller owns yaw/tilt; camera independent"
    profile = _profile(1.0, cfg)
    zeros = [0.0]*(cfg["radial_steps"]+1)
    target_grid = _gore_grid(cfg, profile, zeros, 1.0)
    target_area = _gore_area(target_grid)
    target_lengths = [_cross_length(cfg, profile, i/cfg["radial_steps"], 0.0, 1.0)
                      for i in range(cfg["radial_steps"]+1)]
    vertices, faces, face_uv = _canopy_topology(cfg)
    canopy = _mesh("Canopy", vertices, faces, materials["cloth_outer"], root)
    canopy.data.materials.append(materials["cloth_inner"])
    uv = canopy.data.uv_layers.new(name="GoreAtlas")
    for polygon, coordinates in zip(canopy.data.polygons, face_uv):
        for loop, coordinate in zip(polygon.loop_indices, coordinates):
            uv.data[loop].uv = coordinate
    # A separate rest-pattern UV is measured in metres on each flat cut gore.
    # Print UV stays rectangular/fixed; fabric threads keep a physical pitch.
    rest_uv=canopy.data.uv_layers.new(name="FabricRest")
    for polygon, coordinates in zip(canopy.data.polygons,face_uv):
        panel=min(cfg["gores"]-1,int(sum(u for u,v in coordinates)/len(coordinates)*cfg["gores"]))
        for loop,(u,v) in zip(polygon.loop_indices,coordinates):
            cross=u*cfg["gores"]-panel
            radius,_=_profile_sample(profile,v)
            width=2*radius*math.sin(math.pi/cfg["gores"])
            rest_uv.data[loop].uv=((cross-.5)*width+panel*.137,v*cfg["rib_length"]+panel*.071)
    canopy.data.uv_layers.active_index=0
    # Keep a supported normal change at each stitched rib, instead of smoothing
    # the eight gores into one continuous injection-moulded circular shell.
    circumference=cfg["gores"]*cfg["cross_steps"]
    for edge in canopy.data.edges:
        a,b=edge.vertices
        if a==0 or b==0:
            other=b if a==0 else a
            sharp=(other-1)%cfg["cross_steps"]==0
        else:
            ja,jb=(a-1)%circumference,(b-1)%circumference
            sharp=ja==jb and ja%cfg["cross_steps"]==0
        if sharp:edge.use_edge_sharp=True
    solid = canopy.modifiers.new("ClothThickness", "SOLIDIFY")
    solid.thickness = cfg["cloth_thickness"]
    solid.offset = -1.0
    solid.material_offset = 1
    solid.material_offset_rim = 1
    solid.use_even_offset = True
    # Fixed dense topology resolves cloth tension; no temporal remeshing.
    ribs, seams, stretchers, tips = [], [], [], []
    for k in range(cfg["gores"]):
        ribs.append(_curve(f"Rib_{k:02d}", [(0,0,0)]*(cfg["radial_steps"]+1),
                           cfg["rib_radius"], materials["metal"], root))
        seams.append(_curve(f"Seam_{k:02d}", [(0,0,0)]*(cfg["radial_steps"]+1),
                            cfg["seam_radius"], materials["seam"], root))
        stretchers.append(_cylinder(f"Stretcher_{k:02d}", cfg["stretcher_radius"],
                                    cfg["stretcher_length"], materials["metal"], root, sides=10))
        tips.append(_tip(f"Tip_{k:02d}", materials["metal"], root))
    hem = _curve("SewnHem", [(0,0,0)]*(cfg["gores"]*cfg["cross_steps"]),
                 cfg["hem_radius"], materials["seam"], root, cyclic=True)
    shaft = _cylinder("Shaft", 0.0060, 1.01, materials["metal"], root, z=0.735, sides=24)
    _cylinder("CrownHub", 0.0180, 0.024, materials["metal"], root, z=1.187, sides=24)
    _cylinder("TopFerrule", 0.0090, 0.060, materials["metal"], root, z=1.230, sides=24)
    runner = _cylinder("Runner", 0.016, 0.045, materials["metal"], root, sides=24)
    handle_points = [(0.0, 0.0, 0.29), (0.0, 0.0, 0.13)]
    for i in range(1,97):
        angle = math.pi*i/96
        handle_points.append((0.0, -0.09+0.09*math.cos(angle), 0.13-0.09*math.sin(angle)))
    handle_points.append((0.0,-0.18,0.18))
    handle = _curve("JHandle", handle_points, 0.0215, materials["grip"], root)
    handle.data.bevel_resolution = 5
    attachments=_sewn_parts(materials,root,cfg)
    # One curve contains small detached thread segments, not a painted dotted line.
    stitch_data = bpy.data.curves.new("TwinNeedleThreads", "CURVE")
    stitch_data.dimensions = "3D"
    stitch_data.resolution_u = 1
    stitch_data.bevel_depth = 0.00010
    stitch_data.bevel_resolution = 0
    stitch_data.use_fill_caps = True
    stitch_object = bpy.data.objects.new("TwinNeedleThreads", stitch_data)
    bpy.context.collection.objects.link(stitch_object)
    stitch_object.parent = root
    stitch_data.materials.append(materials.get("thread",materials["seam"]))
    stitch_specs = []
    pitch = 0.0036/cfg["rib_length"]
    for gore in range(cfg["gores"]):
        for side in [0,1]:
            for index in range(int(0.90/pitch)):
                start = 0.08+index*pitch
                stop = start+pitch*0.53
                rest_radius,_=_profile_sample(profile,(start+stop)*.5)
                rest_width=2*rest_radius*math.sin(math.pi/cfg["gores"])
                fraction=min(.20,.0022/rest_width)
                cross=fraction if side==0 else 1-fraction
                spline = stitch_data.splines.new("POLY")
                spline.points.add(2)
                stitch_specs.append((gore,cross,start,stop))
    rig = {"root":root, "attachments":attachments, "stitches":stitch_object, "stitch_specs":stitch_specs, "canopy":canopy, "ribs":ribs, "shaft":shaft,
           "Jhandle":handle, "runner":runner, "stretchers":stretchers,
           "tips":tips, "seams":seams, "hem":hem, "config":cfg,
           "measurements":{}, "openness":-1.0,
           "_target_area":target_area, "_target_lengths":target_lengths}
    update_opening(rig, 1.0)
    return rig


def update_opening(rig, openness):
    """Resolve any state directly; forward/reverse calls have no history."""
    cfg = rig["config"]
    a = _clamp(openness)
    if abs(a-rig["openness"]) < 1e-12:
        return
    profile, amplitudes, grid, area = _fold_state(cfg, a, rig["_target_lengths"], rig["_target_area"])
    rig["_profile"], rig["_amplitudes"], rig["openness"] = profile, amplitudes, a
    coordinates = [(0.0,0.0,cfg["crown_z"])]
    for i in range(1,cfg["radial_steps"]+1):
        for k in range(cfg["gores"]):
            for j in range(cfg["cross_steps"]):
                coordinates.append(_point(cfg,profile,i/cfg["radial_steps"],j/cfg["cross_steps"],k,amplitudes[i],a))
    for vertex, point in zip(rig["canopy"].data.vertices, coordinates):
        vertex.co = point
    rig["canopy"].data.update()
    attach_r, attach_z = _profile_sample(profile, cfg["stretcher_attach_s"])
    reach2 = cfg["stretcher_length"]**2-attach_r**2
    if reach2 <= 0.0:
        raise ValueError("Stretcher cannot reach rib: canonical dimensions violate the linkage")
    runner_z = attach_z-math.sqrt(reach2)
    rig["runner"].location.z = runner_z
    strut_errors = []
    for k in range(cfg["gores"]):
        phi = TAU*(k-0.5)/cfg["gores"]
        cp, sp = math.cos(phi), math.sin(phi)
        rib_points = [(r*cp, r*sp, z) for r,z in profile]
        # The rib keeps its exact length inside the external fabric skin.
        _set_curve(rig["ribs"][k], rib_points)
        seam_points = []
        for i in range(cfg["radial_steps"]+1):
            s = i/cfg["radial_steps"]
            x,y,z = _point(cfg, profile, s, 0.0, k, amplitudes[i], a)
            nr,nz = _normal_rz(profile,s)
            lift = cfg["seam_radius"]*0.45
            seam_points.append((x+cp*nr*lift, y+sp*nr*lift, z+nz*lift))
        _set_curve(rig["seams"][k], seam_points)
        endpoint = Vector((attach_r*cp, attach_r*sp, attach_z))
        base = Vector((0.0,0.0,runner_z))
        delta = endpoint-base
        strut = rig["stretchers"][k]
        strut.location = (endpoint+base)*0.5
        strut.rotation_mode = "QUATERNION"
        strut.rotation_quaternion = delta.to_track_quat("Z", "Y")
        strut_errors.append(abs(delta.length-cfg["stretcher_length"]))
        tip = rig["tips"][k]
        tip.location = Vector(rib_points[-1])
        tip.rotation_mode = "QUATERNION"
        tip.rotation_quaternion = (Vector(rib_points[-1])-Vector(rib_points[-2])).to_track_quat("Z","Y")
    hem_points = []
    for k in range(cfg["gores"]):
        phi = TAU*k/cfg["gores"]
        cp,sp=math.cos(phi),math.sin(phi)
        hem_points += [(cp*x-sp*y,sp*x+cp*y,z) for x,y,z in grid[-1][:-1]]
    _set_curve(rig["hem"], hem_points)
    rib_arc = sum(math.hypot(profile[i+1][0]-profile[i][0], profile[i+1][1]-profile[i][1])
                  for i in range(cfg["radial_steps"]))
    rig["measurements"] = {
        "openness":a, "gores":cfg["gores"], "rib_arc_length_m":rib_arc,
        "rib_length_error_m":abs(rib_arc-cfg["rib_length"]),
        "stretcher_length_m":cfg["stretcher_length"],
        "max_stretcher_error_m":max(strut_errors), "runner_z_m":runner_z,
        "cloth_area_m2":area*cfg["gores"],
        "target_cloth_area_m2":rig["_target_area"]*cfg["gores"],
        "cloth_area_ratio":area/rig["_target_area"],
        "max_fold_depth_m":max(amplitudes),
        "surface_method":"area-constrained deterministic accordion, not collision-solved cloth",
        "topology_vertices":len(coordinates), "topology_faces":len(rig["canopy"].data.polygons),
    }
    for obj,specs in rig.get("attachments",[]):
        for vertex,(gore,cross,s,lift) in zip(obj.data.vertices,specs):
            point=sample_surface(rig,gore,cross,s)
            nr,nz=_normal_rz(profile,s)
            phi=TAU*((gore+cross-.5)/cfg["gores"])
            vertex.co=point+Vector((nr*math.cos(phi)*lift,nr*math.sin(phi)*lift,nz*lift))
        obj.data.update()
    # Threads resolve from the same cloth state and UV location on every seek.
    for spline, (gore,cross,start,stop) in zip(rig["stitches"].data.splines,rig["stitch_specs"]):
        phi = TAU*((gore+cross-0.5)/cfg["gores"])
        for point, s in zip(spline.points,[start,(start+stop)/2,stop]):
            q = s*cfg["radial_steps"]
            i = min(cfg["radial_steps"]-1,int(q));f=q-i
            amp=amplitudes[i]*(1-f)+amplitudes[i+1]*f
            x,y,z=_point(cfg,profile,s,cross,gore,amp,a)
            nr,nz=_normal_rz(profile,s)
            lift=0.00065
            point.co=(x+nr*math.cos(phi)*lift,y+nr*math.sin(phi)*lift,z+nz*lift,1.0)
    rig["root"]["openness"] = a
    rig["root"]["rib_arc_length_m"] = rib_arc
    rig["root"]["cloth_area_ratio"] = area/rig["_target_area"]

