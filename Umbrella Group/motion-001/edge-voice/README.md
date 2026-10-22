# Voz selecionada — Thalita, pt-BR

Em 22/10/2026, o usuário rejeitou Kokoro e a amostra Qwen3-TTS como artificiais. Autorizou expressamente um teste gratuito pela internet, sem conta, e escolheu **Thalita** após comparar com Francisca. Essa autorização substitui a exigência de geração totalmente offline apenas para a voz. Montagem, Blender e exportação continuam locais.

O áudio completo selecionado é `thalitamultilingual-full.mp3`. O JSON adjacente preserva texto, voz, ritmo e os tempos de palavras recebidos do serviço. Os MP3s curtos são as amostras comparadas. A gravação exportada permite remontar o Reel offline.

## Reproduzir, a partir da raiz Umbrella Group

```powershell
python -m venv motion-001/edge-voice/.venv
& motion-001/edge-voice/.venv/Scripts/python.exe -m pip install -r motion-001/edge-voice/requirements.txt
& motion-001/edge-voice/.venv/Scripts/python.exe motion-001/edge-voice.py --full
python motion-001/assemble_edge_voice.py --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
python motion-001/prepare_v7.py
```

No Mac/Linux, use `.venv/bin/python` e `--ffmpeg ffmpeg`. Com os MP3s já presentes, pule os três primeiros comandos: a montagem é offline e não precisa instalar Qwen ou baixar seus pesos.

Cliente [edge-tts](https://github.com/rany2/edge-tts), versão 7.3.1, LGPL-3.0. É um projeto independente que acessa o serviço online Read Aloud do Microsoft Edge; não é SDK oficial com SLA. A licença do cliente não substitui os termos do serviço. Não foi usada chave Azure, conta, assinatura ou cobrança. Nenhum termo foi aceito em nome do usuário. Disponibilidade e vozes podem mudar; os áudios e metadados desta versão ficam preservados.

## Revisão V7.1

O usuário aprovou a base e pediu mais velocidade/entusiasmo e mensagem direta. `thalitamultilingual-v7-1.mp3` / JSON têm a nova fala, ritmo +18%, pitch +4 Hz e tempos WordBoundary. Gerar novamente com `python motion-001/edge-voice.py --revision`; montar com `python motion-001/assemble_edge_voice.py --revision --ffmpeg ffmpeg`. As gravações anteriores permanecem preservadas. Não houve mudança de voz nem serviço pago.
