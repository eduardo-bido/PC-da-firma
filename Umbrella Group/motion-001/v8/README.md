# V8 — gancho de queda, tensão sonora e marca no cenário

## Exportação atual

`motion-001-v8-1080x1920.mp4` e `motion-001-v8-540x960.mp4`: 20,0417 s, 481 quadros, 24 fps, H.264/AAC e Rec.709. Decodificação integral dos dois arquivos sem erros. A ponteira desce 165 px em 0,35 s; o teste de continuidade verifica todos os 193 quadros entre 12 s e fim, com máximo delta 0,524. `verification.json`, `creative-verification.json` e `audio-verification.json` registram os resultados. Não são aprovação criativa nem prova de retenção.

Esses MP4s, a mixagem Foley e o arquivo de referência ficam **apenas no computador de trabalho**: a aprovação automática rejeitou sua inclusão no Git público por não haver licença identificada para o efeito indicado. O Git conserva o render visual silencioso, código, voz, assets CC0, relatórios e imagens. Em outro computador, fornecer `--reference CAMINHO_DO_AUDIO_AUTORIZADO` à preparação. O código não obtém nem publica a referência automaticamente.

## Aprovação em 23/10/2026

Usuário aprovou produzir a direção analisada: queda perceptível nos primeiros 0,35 s, entrada progressiva em super slow motion, som de ar que se concentra/sobe suavemente, redução breve antes do contato e marca Umbrella fosca na parede com profundidade de campo real. Preservar tomada contínua, guarda-chuva existente, voz Thalita, mensagem V7.1, abertura, balanço e duração de 20,0417 s. Nenhuma publicação, conta, cobrança, crédito ou alteração de produção.

## Método

- `render_3d_v8.py` reutiliza a cena V7.1. A câmera demora 0,32 s para começar a acompanhar verticalmente a ponteira; recupera o acompanhamento até 1,2 s. A lente/dolly e todo comportamento após 5 s permanecem da base aprovada.
- O relógio da queda percorre metade do tempo físico em 0,35 s; desacelera continuamente até o contato em 5 s. A interpolação é contínua em posição/velocidade.
- A aplicação da parede amostra o alfa exato do wordmark no atlas existente `source/umbrella-print-atlas.png` (bbox 102,725–411,782). Sem redesenho, fonte substituta ou novo master. Material fosco, iluminação da parede e posição fixa no mundo; saída do enquadramento durante o macro, retorno natural no plano aberto.
- Cycles/OptiX 24 amostras, denoise; reutilização persistente de dados desabilitada para reduzir a condição associada aos dois flashes anteriores. Uma verificação temporal da exportação permanece necessária.
- `prepare_v8.py` preserva os arquivos da voz e legendas V7.1 por cópia. Chama **`design_v8_reference.py`**, revisão sonora vigente. A primeira proposta discreta foi rejeitada como distante; a segunda, `design_v8_cinema.py`/`sound-cinema-v2.wav`, também foi rejeitada como robótica. Não reutilizar essas propostas como aprovadas.
- O usuário forneceu o efeito exato [Slow Motion Sound Effect — twonxd](https://www.youtube.com/watch?v=z_epWpdsHJc). A revisão `reference-v3` usa esse clip de 4,226 s a partir de 0,65 s **sem alterar pitch ou tempo**, com volume e pequenas entradas/saídas. A descrição não informa licença de reutilização; o arquivo não é apresentado como CC0 nem como liberado para postagem. Procedência em `../source/audio/reference-slow-motion-provenance.json`.
- Contatos sintetizados e camada grave sintética foram removidos. Os contatos usam gravação real CC0 de LewisEmmott5; a abertura continua a gravação real CC0 de bewareofkites20. Ar inicial e balanço usam gravações CC0 de KVV_Audio e jackhilton, sem modulação ou time stretch. Qat e o processamento da segunda tentativa ficam documentados como pesquisa rejeitada. Fontes/hashes em `../source/audio/v8-sfx-manifest.json`; licenças distintas em `../source/audio/LICENSE-V8.md`.
- Silêncio de 4,92 a 5 s, contato em 5 s, abertura em 5,30–5,83 s, contatos e balanço sincronizados. Efeitos recuam durante a fala. O terceiro toque suave é estilização de assentamento, sem adicionar um terceiro quique à coreografia visual. Não é gravação física da queda. Medidas em `sound-design.json`; avaliação auditiva do usuário permanece necessária.

## Reprodução

Runtime existente e versões em `../hyperframes-v7/README.md`. Não precisa gerar outra voz ou instalar Qwen. O projeto `hyperframes-v8` usa dependências próprias se instaladas; alternativamente usa o runtime já fixado na pasta irmã V7.

```powershell
npm.cmd ci --prefix motion-001/hyperframes-v7 --ignore-scripts
& 'C:/Program Files/Blender Foundation/Blender 4.3/blender.exe' -b -t 8 -P motion-001/render_3d_v8.py -- --out motion-001/v8-frames-1080 --all --width 1080 --height 1920 --samples 24
python motion-001/prepare_v8.py --frames motion-001/v8-frames-1080 --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe' --reference CAMINHO_DO_AUDIO_AUTORIZADO
Push-Location motion-001/hyperframes-v8
node run.mjs check --json --samples 7
node run.mjs render --fps 24 --quality delivery --workers 2 --output ../v8/motion-001-v8-1080x1920.mp4
Pop-Location
python motion-001/finish_v7.py --version v8 --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe' --ffprobe 'motion-001/hyperframes-v7/node_modules/@ffprobe-installer/win32-x64/ffprobe.exe'
python motion-001/verify_v8.py --ffmpeg 'C:/Program Files/ShareX/ffmpeg.exe'
```

No Mac/Linux adaptar executáveis e caminhos; CUDA/OptiX é específico do Windows/NVIDIA testado. Pacotes Python necessários à montagem: NumPy e Pillow, conforme ambiente existente. Quadros intermediários e dependências ficam fora do Git. A tomada MP4 exportada permite montar sem recalcular o 3D.

Para ajustar apenas o som, executar `python motion-001/design_v8_reference.py --ffmpeg CAMINHO_DO_FFMPEG` e repetir a montagem HyperFrames e a finalização. Não é necessário renderizar o 3D novamente. `--reference CAMINHO.m4a` permite indicar o arquivo de referência. Os arquivos CC0 já estão incluídos; `../source/audio/fetch_v8_sfx.py` documenta a obtenção sem conta.

## Avaliação

Conferir deslocamento da ponteira no primeiro 0,35 s, entrada contínua no slow motion, reconhecimento da marca sem cobrir o cabo, saída no macro, impacto em 5 s e legibilidade no celular. Ouvir em volume confortável, em mono e no alto-falante do celular: tensão sem assobio/aspereza, contato sem clipping, abertura como alívio e voz preservada. O agente não tem audição efetiva da mixagem; métricas técnicas não comprovam sensação sonora. Versões V7/V7.1 permanecem preservadas. Não alegar melhoria de retenção sem dados publicados pelo usuário.

Identidade: Umbrella 01 → 02 → 03. A cena usa a reconstrução existente da LP, não um master 3D proprietário recuperado.
