"""Motion-only controller for the existing Umbrella reconstruction.

World floor is Z=0. Lengths are metres, times are seconds. No asset is rebuilt.
Fall follows a ballistic simulation clock; opening is the original linkage.
The settle is a reduced rolling-body model, not a certified rigid-body/cloth
simulation: gravity acts on a chosen centre of mass over the actual mesh's
support envelope. This gives changing contact points and non-sinusoidal motion.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

_spec = importlib.util.spec_from_file_location(
    "umbrella_v6_geometry", Path(__file__).resolve().parent / "source" / "geometry.py")
geometry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(geometry)

CONTACT_TIME = 4.90
OPEN_START = 5.00
OPEN_END = 5.30
SETTLE_START = 5.30
FINAL_YAW_DEG = 35.0  # After the upside-down transform, gore 0 faces azimuth -35°.
INITIAL_YAW_DEG = -10.0
FLOOR_Z = 0.0
CONTACT_EPSILON = 0.00015
PIVOT = Vector((0.0, 0.0, 1.26))  # Real end of the source TopFerrule.
GRAVITY = 9.81
FALL_HEIGHT = 2.20
FALL_INITIAL_SPEED = 0.70
_PHYSICAL_HIT = (-FALL_INITIAL_SPEED + math.sqrt(
    FALL_INITIAL_SPEED ** 2 + 2 * GRAVITY * FALL_HEIGHT)) / GRAVITY


def clamp(x):
    return min(1.0, max(0.0, float(x)))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def fall_clock(t):
    """C1 continuous editorial slow motion with nonzero impact velocity."""
    t = min(CONTACT_TIME, max(0.0, t))
    times = (0.0, 1.25, 3.35, CONTACT_TIME)
    values = (0.0, .28, .58, _PHYSICAL_HIT)
    slopes = (.26, .20, .026, .012)
    i = next((i for i in range(3) if t <= times[i + 1]), 2)
    d = times[i + 1] - times[i]
    u = (t - times[i]) / d
    return ((2*u**3 - 3*u*u + 1) * values[i]
            + (u**3 - 2*u*u + u) * d * slopes[i]
            + (-2*u**3 + 3*u*u) * values[i + 1]
            + (u**3 - u*u) * d * slopes[i + 1])


def fall_height(t):
    s = fall_clock(t)
    return max(0.0, FALL_HEIGHT - FALL_INITIAL_SPEED*s - .5*GRAVITY*s*s)


def _mesh_points(obj):
    points = np.empty(len(obj.data.vertices) * 3, dtype=np.float64)
    obj.data.vertices.foreach_get("co", points)
    points = points.reshape(-1, 3)
    m = np.array(obj.matrix_basis, dtype=np.float64)
    return points @ m[:3, :3].T + m[:3, 3]


def _support_points(rig):
    """Use the real canopy skin, ferrule cap, rib tips and crown hub."""
    # Newly created and reposed ferrules must expose current local matrices.
    # Otherwise a first scene build can sample the identity matrix for a tip.
    bpy.context.view_layer.update()
    items = [rig["canopy"], *rig["tips"]]
    items.extend(obj for obj in rig["root"].children
                 if obj.name in {"TopFerrule", "CrownHub"})
    points = np.concatenate([_mesh_points(obj) for obj in items])
    return points - np.array(PIVOT)


def _rolling_model(open_points):
    # COM and inertia are explicit shot parameters, because the reconstruction
    # has no measured material masses. The support shape itself is not guessed.
    com_height = .40
    inertia_per_mass = .25
    angles = np.linspace(-math.radians(42), math.radians(42), 673)
    sampled = open_points[::4]
    support = np.array([-np.min(sampled[:, 0]*math.sin(a)
                               - sampled[:, 2]*math.cos(a)) for a in angles])
    potential_height = support + com_height*np.cos(angles)
    # Cloth/rubber compliance rounds the otherwise infinitely sharp transition
    # from the ferrule cap to the canopy. Geometry contact still uses exact data.
    sigma = math.radians(.8) / (angles[1] - angles[0])
    axis = np.arange(-math.ceil(4*sigma), math.ceil(4*sigma) + 1)
    kernel = np.exp(-.5*(axis/sigma)**2)
    kernel /= kernel.sum()
    pad = len(kernel)//2
    potential_height = np.convolve(np.pad(potential_height, (pad, pad), mode="edge"),
                                   kernel, mode="valid")
    gradient = np.gradient(potential_height, angles)
    dt = 1 / 480
    times = np.arange(0, 10.01, dt)
    theta, omega = math.radians(1), 1.0
    lean, speed = [], []
    for elapsed in times:
        lean.append(theta)
        speed.append(omega)
        damping = 1.2 if elapsed < .7 else 4.0
        acceleration = (-GRAVITY*np.interp(theta, angles, gradient)/inertia_per_mass
                        - damping*omega - .07*math.tanh(omega/.02))
        omega += acceleration*dt
        theta += omega*dt
    lean = np.asarray(lean)
    # Detect the first new canopy support and the following return to the tip.
    # The source ferrule is a 9 mm-radius cap: its edge already raises the
    # shaft centre when tilted. Subtract that before detecting NEW cloth contact.
    rises = np.interp(lean, angles, support) - .009*np.abs(np.sin(lean))
    events = []
    above = False
    for t, h in zip(times, rises):
        now = h > .0008
        if now != above and t > .1:
            events.append(float(t))
        above = now
        if len(events) >= 2:
            break
    return {"times": times, "lean": lean, "speed": np.asarray(speed),
            "events": events, "max_tilt_deg": float(np.degrees(lean).max()),
            "com_height_m": com_height, "inertia_per_mass": inertia_per_mass}


def prepare_motion(rig):
    if "_v6_model" in rig:
        return
    old = rig["openness"]
    geometry.update_opening(rig, 1.0)
    rig["_v6_open_points"] = _support_points(rig)
    rig["_v6_model"] = _rolling_model(rig["_v6_open_points"])
    geometry.update_opening(rig, old)
    rig["_v6_points_openness"] = None


def _ballistic_bounce(elapsed, duration):
    if 0 < elapsed < duration:
        return .5 * GRAVITY * elapsed * (duration - elapsed)
    return 0.0


def opening(t):
    if t < OPEN_START:
        return 0.0
    if t < OPEN_END:
        # Full mechanical travel is seven 24 fps frames; most motion occurs in
        # the central four frames. A readable tension-build precedes the snap.
        u = clamp((t - OPEN_START) / (OPEN_END - OPEN_START))
        return smooth(u)**.72
    # Small one-cycle spring response, not a second slow opening.
    u = (t - OPEN_END) / .16
    if u < 1:
        return 1 - .012*math.sin(math.pi*u)**2
    return 1.0


def apply_motion(t, rig):
    """Pose the original rig, return camera/foley/diagnostic landmarks."""
    prepare_motion(rig)
    a = opening(t)
    geometry.update_opening(rig, a)
    if rig.get("_v6_points_openness") != a:
        rig["_v6_points"] = (_support_points(rig) if a != 1.0
                             else rig["_v6_open_points"])
        rig["_v6_points_openness"] = a
    points = rig["_v6_points"]
    elapsed = max(0.0, t - SETTLE_START)
    model = rig["_v6_model"]
    if t < CONTACT_TIME:
        physical = fall_clock(t) / _PHYSICAL_HIT
        theta = math.radians(-12 + 13*physical)
        yaw = math.radians(INITIAL_YAW_DEG - 15 + 15*physical)
        gap = fall_height(t)
        phase = "fall"
    else:
        theta = math.radians(1)
        yaw = math.radians(INITIAL_YAW_DEG)
        gap = _ballistic_bounce(t - CONTACT_TIME, .09)
        phase = "contact" if t < OPEN_START else "opening"
        if t >= SETTLE_START:
            theta = float(np.interp(elapsed, model["times"], model["lean"]))
            spin = 1 - math.exp(-1.8*elapsed)
            yaw = math.radians(INITIAL_YAW_DEG + (FINAL_YAW_DEG-INITIAL_YAW_DEG)*spin)
            for index, event in enumerate(model["events"]):
                gap += _ballistic_bounce(elapsed - event, .070 if index == 0 else .040)
            phase = "settling" if elapsed < 2.5 else "rest"
    rotation = (Quaternion((1, 0, 0), math.pi)
                @ Quaternion((0, 0, 1), yaw)
                @ Quaternion((0, 1, 0), theta))
    rot = rotation.to_matrix()
    normal = np.asarray(rot[2], dtype=np.float64)
    local_lowest = float(np.min(points @ normal))
    # A few millimetres of rolling translation, growing only as a physical
    # canopy support develops. The hero's world position stays predictable.
    roll_distance = .035 * (1 - math.cos(theta))
    x = roll_distance*math.cos(-yaw)
    y = roll_distance*math.sin(-yaw)
    lift = FLOOR_Z + CONTACT_EPSILON - local_lowest + gap
    matrix = (Matrix.Translation((x, y, lift))
              @ rot.to_4x4() @ Matrix.Translation(-PIVOT))
    rig["root"].matrix_world = matrix
    tip_position = matrix @ PIVOT
    state = {
        "tip_position": tip_position,
        "crown_position": matrix @ Vector((0, 0, rig["config"]["crown_z"])),
        "handle_position": matrix @ Vector((0, -.09, .08)),
        "brand_position": matrix @ Vector((.405, 0, .88)),
        # Print alpha bbox centre is y=753.5/1024 in the verified atlas.
        # Invert the source shader's UV transform to land on the real fabric,
        # rather than focusing on the interior framing landmark above.
        "brand_focus": matrix @ geometry.sample_surface(rig,0,.50067,.74644),
        "openness": a, "contact": gap <= .0002,
        "yaw": yaw, "tilt": theta, "ground_gap": gap,
        "impact_events": [CONTACT_TIME] + [SETTLE_START + v for v in model["events"]],
        "phase": phase, "matrix": matrix,
        "max_tilt_deg": model["max_tilt_deg"],
    }
    rig["_v6_state"] = state
    return state


def diagnostics(rig):
    """Small serializable evidence for the shot's reproducibility report."""
    prepare_motion(rig)
    model = rig["_v6_model"]
    return {
        "floor_z_m": FLOOR_Z, "contact_clearance_m": CONTACT_EPSILON,
        "fall_physical_duration_s": _PHYSICAL_HIT,
        "fall_editorial_duration_s": CONTACT_TIME,
        "fall_tip_heights_m": {str(t): fall_height(t) for t in (0, 1.25, 2.7, 3.35, 4, 4.9)},
        "opening_start_s": OPEN_START, "opening_end_s": OPEN_END,
        "max_tilt_deg": model["max_tilt_deg"],
        "impact_events_s": [CONTACT_TIME] + [SETTLE_START + t for t in model["events"]],
        "final_yaw_degrees": FINAL_YAW_DEG,
        "method": "Ballistic fall; source linkage; reduced gravity/support-envelope roll with damping and small ballistic rebounds.",
        "limitation": "Mass/inertia are shot parameters. No cloth self-collision or measured rigid-body mass model.",
    }
