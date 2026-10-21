from pathlib import Path
import importlib.util
import time
import bpy
HERE = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('look',HERE/'lookdev_v6.py')
look=importlib.util.module_from_spec(spec);spec.loader.exec_module(look)
rig,cam,scene=look.scene_setup(540,960,32)
rig['_lights']={}
for name in ('key','side','ferrule','pool','edge','wallwash','warm'):
    bpy.ops.object.light_add(type='AREA')
    o=bpy.context.object;o.hide_render=True;rig['_lights'][name]=o
for t in (9.2,1.0):
    look.base.pose(t,rig,cam)
    scene.render.filepath=str(HERE/'diagnostics'/f'look-v6-{t}.png')
    start=time.perf_counter()
    bpy.ops.render.render(write_still=True)
    print('V6_LOOK_SECONDS',t,time.perf_counter()-start,flush=True)
