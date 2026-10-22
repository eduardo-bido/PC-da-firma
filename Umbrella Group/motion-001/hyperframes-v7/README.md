# V7 — tomada contínua, voz e legenda

**Estado de revisão:** a voz de teste foi rejeitada. A tomada base está renderizada, mas não existe final narrado V7 aprovado. A pesquisa solicitada em seguida está em `../REFERENCIAS_V7.md`. Os comandos abaixo descrevem a implementação de teste; não significam aprovação de sua voz ou acabamento.

Teste da direção descrita pelo usuário em 22/10/2026. A V6 foi rejeitada. Leia `SPEC.md` antes de editar.

## Produção local

Blender 4.3.2 faz a tomada; **HyperFrames 0.8.184** monta mídia, narração, legendas e título. **Kokoro ONNX 0.4.9**, voz feminina `pf_dora`, gera a fala offline. Não exige conta, login HeyGen, API ou créditos. Downloads iniciais dos pacotes/pesos precisam de internet; a geração e o render usam arquivos locais. A aplicação desktop HyperFrames não foi instalada.

Testado neste Windows com Node 26.7, Python 3.12, RTX 3060 Ti e FFmpeg do ShareX. CLI requer Node 22+. O projeto mantém `package-lock.json`; use `npm ci`, sem atualizar versões durante uma revisão.

### Preparação, na raiz Umbrella Group

```powershell
python -m pip install -r motion-001/requirements.txt
python -m venv motion-001/local-tts/.venv
& motion-001/local-tts/.venv/Scripts/python.exe -m pip install -r motion-001/local-tts/requirements.txt
python motion-001/local-tts/download_models.py
& motion-001/local-tts/.venv/Scripts/python.exe motion-001/local-tts/narrate.py
npm.cmd ci --prefix motion-001/hyperframes-v7 --ignore-scripts
```

No Mac/Linux, use `python3` e `motion-001/local-tts/.venv/bin/python`; não reutilize o caminho de Blender/FFmpeg do Windows. As dependências nativas de voz incluem eSpeak NG, carregado pelo pacote Python. Nesta sandbox, carregar sua DLL temporária exigiu execução autorizada fora da restrição; isso não é serviço remoto. `narrate.py` adapta o tipo `speed` à declaração ONNX para contornar incompatibilidade observada no pacote 0.4.9.

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
- Kokoro ONNX: MIT, [wrapper](https://github.com/thewh1teagle/kokoro-onnx). Pesos Kokoro 82M: Apache-2.0, [model card](https://huggingface.co/hexgrad/Kokoro-82M). Voz portuguesa feminina `pf_dora` está na [lista oficial](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). O próprio autor registra limites de qualidade em idiomas não ingleses.
- eSpeak NG/phonemizer: componentes GPL de pronúncia local, nas dependências Python. Não redistribuímos ambiente nem DLLs pelo Git.
- FFmpeg instalado nesta máquina: build GPL. Wrapper `@ffprobe-installer/ffprobe` LGPL-2.1; binário Windows distribuído por seu pacote GPL-3.0. Verificar a licença do binário na plataforma de destino.
- GSAP 3.14.2: licença própria Standard GSAP, não MIT. Usado para animação de legendas e título; distribuição do pacote segue seus termos.
- Som de abertura CC0 por bewareofkites20, conforme `../source/audio/LICENSE.txt`.
- Manrope e assets LP: fontes existentes do projeto, preservadas. Documentos Umbrella 01 → 02 → 03 continuam superiores à prova de conceito.

Pesos de voz (~354 MB), ambientes, pacotes e quadros intermediários ficam fora do Git. `../local-tts/model-manifest.json` registra as origens e hashes baixados. O projeto não consulta provedores de mídia durante o render.
