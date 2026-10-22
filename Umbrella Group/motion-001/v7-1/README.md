# V7.1 — revisão pontual

Em 22/10/2026 o usuário avaliou positivamente a V7 e pediu três ajustes: eliminar a piscada no guarda-chuva ao final, explicitar a Umbrella como solução e tornar a voz mais rápida/dinâmica. Cena, identidade, câmera, coreografia, sons e duração de 20,0417 s foram preservados.

## Fala

> Você ficou cinco segundos esperando esse contato. Seu site também precisa causar impacto, prender atenção e conquistar clientes. É isso que a gente resolve. Conheça a Umbrella.

Thalita foi mantida. Ritmo do serviço passou de +3% a +18%, com pitch +4 Hz. Não houve aceleração posterior do áudio. Voz gera online pelo serviço gratuito já autorizado; render/montagem locais. Nenhuma conta, custo, crédito ou publicação.

## Correção da piscada

Os PNGs originais, a tomada MP4 e a exportação V7 exibem duas mudanças isoladas de iluminação: quadros **319 (13,2917 s)** e **365 (15,2083 s)**. O salto médio na região do guarda-chuva é cerca de 17 níveis RGB/255, versus ~0,1 nos quadros adjacentes. Não foi detectada troca de sinal nas rotações. Um render em processo Blender novo, com a mesma cena e parâmetros, preservou os quadros vizinhos e corrigiu os dois anômalos. O mecanismo interno exato de estado/cache do renderizador não foi demonstrado.

`repair_v7_frames.py` usa somente os dois quadros novos e preserva os outros 479 PNGs, sem interpolação, congelamento, mudança de câmera ou material. A V7 entregue continua intacta em `../v7/`. `repair-report.json` contém os valores e hashes. `flicker-check.json` verifica o problema no MP4 efetivamente exportado.

## Reproduzir

Primeiro seguir o setup em `../hyperframes-v7/README.md`. O áudio revisado está em `../edge-voice/thalitamultilingual-v7-1.mp3`; não é necessário gerá-lo de novo. Para regeneração opcional da voz, `python ../edge-voice.py --revision`, usando o ambiente com edge-tts.

Da raiz Umbrella Group, com os PNGs V7 presentes:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.3/blender.exe' -b -t 8 -P motion-001/render_3d_v7.py -- --out motion-001/v7-flash-repro --frames 318,319,320,364,365,366 --width 1080 --height 1920 --samples 24
python motion-001/repair_v7_frames.py
python motion-001/assemble_edge_voice.py --revision --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
python motion-001/prepare_v7.py --frames motion-001/v7-1-frames-1080 --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
Push-Location motion-001/hyperframes-v7
node run.mjs check --json --samples 7
node run.mjs render --fps 24 --quality delivery --workers 2 --output ../v7-1/motion-001-v7-1-1080x1920.mp4
Pop-Location
python motion-001/finish_v7.py --version v7-1 --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe' --ffprobe 'motion-001/hyperframes-v7/node_modules/@ffprobe-installer/win32-x64/ffprobe.exe'
python motion-001/diagnostics/verify_v7_1_flicker.py
```

Os PNGs completos não ficam no Git. A tomada corrigida já está em `../hyperframes-v7/assets/continuous-take.mp4`, suficiente para montar novamente sem render 3D. Para reconstruir os PNGs, seguir o comando completo Blender da V7. No Mac/Linux, adaptar executáveis; o teste desta correção ocorreu no Windows/RTX 3060 Ti.

Identidade permanece subordinada a Umbrella 01 → 02 → 03. Nenhum master ausente foi redesenhado. O usuário aprovou a direção visual V7; a fala e a revisão V7.1 ainda precisam de avaliação. O agente não ouviu a nova mixagem; os tempos das legendas vêm dos marcadores de palavra do serviço.
