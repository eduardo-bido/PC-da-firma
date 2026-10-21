# Motion001 v6 — studio look audit

Local-only work. No paid rendering, generated image, account, stock download, or production modification.

## Observed v5 problems

- Eight sources plus world illumination filled almost every surface. The floor and front of the canopy became uniformly lavender/grey, obscuring shape and floor contact.
- Large frontal highlight, glossy handle, soft absent contact and empty planes read as CGI. Increasing texture noise would not fix these problems.
- Existing actual LP cloth already contains the project Terlenka diffuse/roughness/normal maps, 0.32/0.34mm yarn structure, sewn-edge puckering and physical ink.
- The old wide view presents a closed umbrella at roughly 8% of portrait frame width. The environment dominates for little informational gain. Lighting improvements cannot repair this framing by themselves.
- The underlying closed fabric remains a deterministic geometric folding approximation, not simulated cloth. That limitation is especially exposed in long closeups of its regular pleats.

## New module

`lookdev_v6.py` exposes `scene_setup(width, height, samples, engine='CYCLES') -> rig, cam, scene`.

- Original geometry builder, original project cloth shader and shot atlas are imported from the existing source path. No asset master was invented or replaced.
- Floor surface at exact Z=0 for the new contact solver. Matte neutral graphite, 0.64–0.76 roughness, 0.12mm fine surface height.
- Warm charcoal backdrop with a 45cm cove and physically placed black shadow flag. Background key produces an optical shadow rather than a texture gradient. The separate wall paint still makes the floor legible.
- Fixed photographic light hierarchy: warm neutral narrow strip key 620W; broad weak neutral fill55W; subtle violet edge85W; overhead silk70W; small warm background key190W.
- Low neutral world ambient, AgX Medium High Contrast, exposure+0.25.
- Existing metal meshes receive a removable 0.35mm/3segment bevel modifier for edge highlights. Identity shape dimensions are unchanged. Handle remains the existing geometry with rougher satin material and microscopic grip texture.
- No pulsing light energies, emissive floor, bloom or cosmetic fog.

## Renderer verified on this PC

Blender4.3.2 lists NVIDIA GeForce RTX3060Ti for CUDA and OptiX and Intel i7-10700F CPU. The module selects OptiX first and can fall back through available GPU backends, finally CPU with an explicit console label.

Test:540×960,32samples,CyclesOptiX,denoising,6maxbounces. First hero4.7s including scene initialization; next closed shot2.3s. Device scene memory approximately465MB. The measurements are examples, not a whole-film ETA; opening deformation and higher resolution may cost more.

Diagnostics were rendered with the old v5 camera at1.0s and9.2s only to compare lighting. They are not the v6 camera design. Files: `look-v6-1.0.png`, `look-v6-9.2.png`. The diagnostic runner uses invisible dummy old lights solely to allow the old pose function to run.

## Remaining evaluation

- Inspect actual v6 camera shots, especially macro tip and printed fabric. Keep physical shadow and contact inside frame.
- Validate low samples do not flicker in video; increase final samples to64 or96 if concrete temporal noise appears. Do not infer temporal quality from one still.
- Preserve recognizable floor geometry, controlled dark values and a distinct violet object when viewed at phone size.
- Material detail at1080 and close range is more meaningful than enlarging weave to survive540 preview.
