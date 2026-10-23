# Umbrella Motion 001 — composição V8

Montagem local com HyperFrames 0.8.184 e GSAP fixados pelo package-lock. Uma tomada 3D, voz Thalita V7.1, som reference-v3 e legendas. As duas tentativas sonoras anteriores foram rejeitadas. A referência de YouTube foi escolhida pelo usuário; a licença de reutilização ainda não foi identificada. Não gera voz nem usa serviço externo durante a renderização.

Método, fontes e reprodução completa em [../v8/README.md](../v8/README.md). Execute nesta pasta:

```powershell
node run.mjs check --json --samples 7
node run.mjs render --fps 24 --quality delivery --workers 2 --output ../v8/motion-001-v8-1080x1920.mp4
```

`run.mjs` usa dependências próprias se disponíveis, ou o runtime V7 da pasta irmã; nesse caso instale com `npm ci --prefix ../hyperframes-v7 --ignore-scripts`. Não execute `npm update`: o lockfile registra o runtime usado. Telemetria desabilitada. Chrome/Chromium, FFmpeg e FFprobe são executáveis locais; caminhos podem ser definidos em `HYPERFRAMES_BROWSER_PATH`, `HYPERFRAMES_FFMPEG_PATH` e `HYPERFRAMES_FFPROBE_PATH`.

`assets/continuous-take.mp4` contém o render físico sem textos; `assets/foley.wav` contém o desenho sonoro separado da voz. Recriar apenas o som não exige novo render 3D. O HTML mantém volume 1 para voz e 0,7 para efeitos.

O render visual silencioso está no Git. O Foley com a referência e os MP4s finais V8 são locais, pois a licença do efeito ainda não foi identificada. Antes dos comandos acima, fornecer um arquivo autorizado: `python ../prepare_v8.py --reference CAMINHO_DO_AUDIO --ffmpeg CAMINHO_DO_FFMPEG`. Isso preserva a tomada já incluída e cria o Foley localmente.
