# V7 — tomada contínua, voz e legenda

**Estado de revisão:** V7 exportada para avaliação. O usuário confirmou guarda-chuva, câmera contínua, voz feminina sem apresentadora e cerca de 20 s. Rejeitou Kokoro e Qwen, autorizou voz online gratuita sem conta e escolheu **Thalita**. A amostra de voz foi escolhida; o vídeo completo não foi aprovado para publicação.

## Produção

Blender 4.3.2 faz a tomada; **HyperFrames 0.8.184** monta mídia, narração, legendas e título. A voz selecionada é `pt-BR-ThalitaMultilingualNeural`, gravada pelo serviço online Edge com autorização explícita. [Áudio e reprodução](../edge-voice/README.md). Com os arquivos fornecidos, montagem e render funcionam offline. Não houve conta, chave API, cobrança ou créditos. A aplicação desktop HyperFrames não foi instalada.

Testado neste Windows com Node 26.7, Python 3.12, RTX 3060 Ti e FFmpeg do ShareX. CLI requer Node 22+. O projeto mantém `package-lock.json`; use `npm ci`, sem atualizar versões durante uma revisão.

### Preparação, na raiz Umbrella Group

```powershell
python -m pip install -r motion-001/requirements.txt
# A gravação selecionada já está no projeto; não precisa gerá-la novamente.
python motion-001/assemble_edge_voice.py --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
npm.cmd ci --prefix motion-001/hyperframes-v7 --ignore-scripts
```

No Mac/Linux, use `python3`, os caminhos locais de Blender/FFmpeg e a gravação existente. Para gerar outra gravação online, siga `../edge-voice/README.md`. Qwen/Kokoro estão preservados apenas como experimentos rejeitados; não são dependências do render da voz escolhida.

### Render e montagem

```powershell
& 'C:/Program Files/Blender Foundation/Blender 4.3/blender.exe' -b -t 8 -P motion-001/render_3d_v7.py -- --out motion-001/v7-frames-1080 --all --width 1080 --height 1920 --samples 24
python motion-001/prepare_v7.py --frames motion-001/v7-frames-1080 --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
Push-Location motion-001/hyperframes-v7
node run.mjs check --json
node run.mjs snapshot --at 0,0.5,4.8,5,5.42,5.7,7,11.5,15,18.5 --describe false
node run.mjs preview
# Depois da revisão visual:
node run.mjs render --fps 24 --quality delivery --workers 2 --output ../v7/motion-001-v7-1080x1920.mp4
Pop-Location
```

`run.mjs` usa somente o CLI local e desabilita telemetria. Detecta Chrome e FFmpeg nos caminhos testados do Windows. Para outra máquina, exporte `HYPERFRAMES_BROWSER_PATH` e `HYPERFRAMES_FFMPEG_PATH` ou deixe os executáveis no PATH. FFprobe vem do pacote local por plataforma. Não há comando de publicação neste fluxo.

## Skills oficiais verificadas

Consultadas: `hyperframes`, `hyperframes-cli`, `media-use` e suas referências de formato, vídeo vertical, legendas, movimento e revisão, no [repositório oficial](https://github.com/heygen-com/hyperframes/tree/main/skills). Não foi instalado um plugin global nesta sessão.

Para instalação opcional das skills no seu agente, em uma sessão com permissão para editar a pasta de skills:

```sh
npx hyperframes@0.8.184 skills update
```

Esse comando oficial instala/atualiza o conjunto central. Não usar `--all` por padrão. Para Claude Code, o README oficial também documenta `claude plugin marketplace add heygen-com/hyperframes` e `claude plugin install hyperframes@hyperframes`. Instalar skills ajuda a orientar o agente; não produz filmagem ou melhora um modelo 3D por si só.

## Licenças e procedência

- HyperFrames: Apache-2.0; código oficial [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes).
- Voz escolhida: cliente edge-tts 7.3.1, LGPL-3.0; serviço online Edge autorizado pelo usuário, separado da licença do cliente. Áudio exportado e documentação em `../edge-voice/`.
- Qwen3-TTS VoiceDesign: código/pesos Apache-2.0, testado e rejeitado; não integra a faixa final.
- Experimento rejeitado — Kokoro ONNX: MIT, [wrapper](https://github.com/thewh1teagle/kokoro-onnx). Pesos Kokoro 82M: Apache-2.0, [model card](https://huggingface.co/hexgrad/Kokoro-82M). Voz portuguesa feminina `pf_dora` está na [lista oficial](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). O próprio autor registra limites de qualidade em idiomas não ingleses.
- eSpeak NG/phonemizer: componentes GPL de pronúncia local, nas dependências Python. Não redistribuímos ambiente nem DLLs pelo Git.
- FFmpeg instalado nesta máquina: build GPL. Wrapper `@ffprobe-installer/ffprobe` LGPL-2.1; binário Windows distribuído por seu pacote GPL-3.0. Verificar a licença do binário na plataforma de destino.
- GSAP 3.14.2: licença própria Standard GSAP, não MIT. Usado para animação de legendas e título; distribuição do pacote segue seus termos.
- Som de abertura CC0 por bewareofkites20, conforme `../source/audio/LICENSE.txt`.
- Manrope e assets LP: fontes existentes do projeto, preservadas. Documentos Umbrella 01 → 02 → 03 continuam superiores à prova de conceito.

Pesos de voz experimentais (Kokoro ~354 MB; Qwen ~4,5 GB), ambientes, pacotes e quadros intermediários ficam fora do Git. `../local-tts/model-manifest.json` registra as origens e hashes baixados. O projeto não consulta provedores de mídia durante o render.

## Revisão mobile

Abra `../review-v7.html` por servidor local ou reproduza o MP4 540×960 no telefone. Conferir movimento em 0,5 s, aproximação até 5 s, contato sem atravessar o piso, abertura até 5,65 s e fala após a abertura. Legendas entre x=130–910 e y≈386–565; título acima. Texto deve ser lido sem pausa em largura de 360 px. Conferir com áudio e sem áudio, volume de fala versus impacto, pronúncia Umbrella e permanência do convite ao perfil. A interface real do Instagram precisa ser conferida pelo usuário antes de postar.

`../v7/verification.json` registra decodificação completa, dimensões, duração, quadros e hashes dos MP4s. `check-report.json` verifica a composição em amostras; não comprova realismo, naturalidade de voz ou conversão. O agente não ouviu a mixagem final; a escolha auditiva do usuário cobriu a amostra Thalita. Limite visual: pregas do tecido fechado na reconstrução. Não é master proprietário recuperado.
