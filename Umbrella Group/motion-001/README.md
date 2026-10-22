# Umbrella Group — Motion 001

## V7 — tomada contínua com narração e legendas

A V6 foi rejeitada em 22/10/2026. A direção vigente é uma aproximação contínua até o contato em cerca de cinco segundos, seguida de voz feminina e legendas conectando atenção a posicionamento digital. O novo projeto usa Blender para a tomada e HyperFrames local para voz gravada em arquivo, legendas e título. A voz de teste Kokoro foi rejeitada por soar robótica e não deve ser usada na entrega final. A prioridade mais recente é a [pesquisa de referências](REFERENCIAS_V7.md). Não há login, chamada paga, publicação ou alteração da LP.

Leia [o roteiro e critérios da V7](hyperframes-v7/SPEC.md) e [os comandos de reprodução](hyperframes-v7/README.md). As decisões ainda não respondidas pelo usuário estão registradas no roteiro; 20 segundos, guarda-chuva e voz sem apresentadora são suposições para o teste. O realismo do tecido fechado continua limitado pela reconstrução disponível.

## V6 — atenção, queda e convite ao perfil

A v6 substitui a câmera da v5 por seis tomadas com lentes fixas: retrato da queda, plano com chão, macro da ponteira, abertura, impressão e hero. A física usa gravidade em um relógio de slow motion, apoio calculado na superfície existente e balanço com amortecimento. A ponteira encontra o piso em Z=0 aos 4,90 s; a abertura acontece entre 5,00 e 5,30 s. Há transferência de apoio durante a inclinação, em vez de manter artificialmente ponta e borda simultaneamente no chão.

A luz usa Cycles, key lateral retangular, pouco preenchimento e fundo ameixa com recorte âmbar. A fonte do fundo ilumina apenas o cenário para evitar uma segunda sombra dura do objeto. Há motion blur de transformação do objeto e das câmeras. A deformação da abertura continua avaliada por quadro pelo rig original; não há simulação de tecido com auto-colisão.

`cloth_pose_v6.py` configura quatro pregas por painel na tomada fechada, usando o mesmo solver de área da reconstrução. Isso alarga as dobras e reduz o aspecto de tubo estriado; o estado aberto, o UV e a impressão permanecem os da fonte. A configuração é local à tomada e não altera `source/geometry.py`.

A mensagem entra em etapas: **“Você esperou a queda.” → “Seu site também precisa prender.” → “E converter.” → “Umbrella”**, assinatura e **“Conheça a Umbrella no perfil”**. O objetivo é visita ao perfil. A pesquisa em [RESEARCH_V6.md](RESEARCH_V6.md) distingue referências visuais de campanhas com resultados documentados; nenhum resultado de conversão da Umbrella está sendo alegado.

O áudio combina uma [abertura real CC0, por bewareofkites20](https://freesound.org/people/bewareofkites20/sounds/148918/), com contatos e texturas procedurais locais. Fonte, MP3 público e WAV decodificado estão em `source/audio/`, com licença. Não houve conta nova, serviço pago nem geração com créditos. Os sons de contato continuam uma interpretação editorial, não uma gravação deste objeto proprietário.

Reprodução, a partir da pasta **Umbrella Group**, com Blender 4.3, Python, NumPy, Pillow e FFmpeg:

```sh
python3 -m pip install -r motion-001/requirements.txt
python3 motion-001/make_shot_atlas.py
blender --background --factory-startup --python motion-001/render_3d_v6.py -- --out motion-001/v6-frames-1080 --all --width 1080 --height 1920 --samples 24
python3 motion-001/assemble_v6.py --frames motion-001/v6-frames-1080 --out motion-001/v6 --ffmpeg "$(command -v ffmpeg)" --font public/fonts/Manrope.ttf
python3 motion-001/verify_v6.py --out motion-001/v6 --ffmpeg "$(command -v ffmpeg)"
```

No Windows, use `python` e os caminhos locais dos executáveis. O render detecta OptiX, CUDA, Metal, HIP ou OneAPI; se nenhum estiver disponível, usa CPU e registra essa escolha. Para revisar primeiro, use `--width 540 --height 960 --samples 32`. `--frames 0,118,128,176,336` renderiza apenas os quadros indicados. `--start` e `--end` dividem um render completo; `--resume` preserva quadros já existentes.

Entregas em `v6/`: `motion-001-v6-1080x1920.mp4`, `motion-001-v6-540x960.mp4`, `hero-frame.png`, `contact-sheet.png` e `sound-mix.wav`. A montagem gera H.264/AAC com faststart, 24 fps e 15 s. Os quadros intermediários novos ficam fora do Git; os scripts e assets permitem recriá-los. Os documentos **01 → 02 → 03** continuam regendo identidade. A reconstrução e a variante de orientação da impressão permanecem documentadas como estudo da LP, sem promoção a master.

Revisão mobile: reconhecer movimento nos primeiros 0,5 s; entender o contato sem som; ler a impressão no insert; ler cada frase sem pausar; conferir a chamada ao perfil acima da interface inferior. O nome e a assinatura ocupam a área central superior no final. Os controles reais da plataforma variam e devem ser conferidos no preview de publicação pelo usuário.

Para a revisão local com botões por tomada e avanço de um quadro, execute `python3 -m http.server 8541 --bind 127.0.0.1` na pasta Umbrella Group e abra `http://127.0.0.1:8541/motion-001/review-v6.html`. O player usa o MP4 reduzido exportado em `v6/`; os arquivos permanecem no computador.

## Corte anterior: v5

O Reel tem **15 s, 24 fps e 9:16**. A v5 responde à revisão do usuário: movimento no primeiro quadro, queda de cerca de 5 s pela ponta da haste, contato macro, abertura em meio segundo, copa invertida que inclina e balança, corte direto para a marca impressa, recuo e assinatura exata. O quadro inicial percorre o tecido durante 0,29 s, e um segundo detalhe de tecido quebra a queda longa. A luz quente fica à esquerda do cenário e a luz violeta cresce à direita na abertura; o piso permanece grafite fosco. A câmera deriva discretamente no fim para que o produto não congele sob o letreiro.

| Tempo | Ação principal |
|---|---|
| 0–0,29 s | Tecido violeta em close já em movimento. |
| 0,29–4,90 s | Queda pela ponta, com inserção de textura e aproximação gradual da câmera. |
| 4,90–5,58 s | Contato com ressalto curto, estalo do mecanismo e abertura rápida. |
| 5,78–7,16 s | Copa inclina, a borda toca o piso e o giro oscila com amortecimento. |
| 7,16–8,12 s | Corte rápido para a impressão “Umbrella” no tecido. |
| 8,12–15 s | Recuo, movimento residual e assinatura em Manrope. |

**Referências de linguagem social:** o [Reel da NYX com objeto descendo e revelação final](https://www.instagram.com/reel/DN3YtLY0Pa5/) foi localizado no [catálogo FOOH](https://fooh.com/library/3410-nyx-smartphone-descends-with-umbrella-fooh-ad). Usei a progressão de escala e o objeto como gancho; não há cópia de cenários, quadros, áudio ou assets. O catálogo o classifica com impacto “Impressive”, mas não fornece uma contagem de visualizações auditável, então não trato sua viralidade como fato confirmado. A [análise oficial da Meta](https://www.facebook.com/business/ads/facebook-instagram-reels-ads) embasa vídeo 9:16 com áudio e marca na zona segura; o [case de ASMR da Sugar Rush Sweeties publicado pelo TikTok](https://ads.tiktok.com/business/en/inspiration/sugar-rush-sweeties-tiktok-success-story?redirected=1) embasa o uso de sons táteis do produto. Essas referências orientam montagem, não prometem alcance.

O objeto e a estampa vêm da **reconstrução V7 da LP**, que continua em revisão e não equivale ao master de marca. O movimento é dirigido por código, com correção de altura para evitar atravessar o piso; o áudio é uma marcação sintética local. Por isso, este MP4 é **prévia editorial**. Os documentos **01 → 02 → 03** mantêm a autoridade de identidade descrita abaixo. Nada foi publicado nem alterou a produção.

Para reproduzir no Mac com Blender 4.3+, Python 3 e FFmpeg local:

```sh
python3 -m pip install -r motion-001/requirements.txt
python3 motion-001/make_shot_atlas.py
blender --background --factory-startup --python motion-001/render_3d_v5.py -- --out motion-001/v5-frames-1080 --all --width 1080 --height 1920 --samples 24
python3 motion-001/assemble_v5.py --frames motion-001/v5-frames-1080 --out motion-001/v5 --ffmpeg "$(command -v ffmpeg)" --font public/fonts/Manrope.ttf
```

Se não houver FFmpeg separado, o Blender pode codificar os mesmos quadros e o WAV:

```sh
python3 motion-001/assemble_v5_blender.py --frames motion-001/v5-frames-1080 --out motion-001/v5 --blender "$(command -v blender)" --font public/fonts/Manrope.ttf
```

No Windows, `ffmpeg.exe` já instalado em `C:\Program Files\ShareX\ffmpeg.exe` funcionou. O script de montagem produz o MP4 **1080 × 1920** e a amostra **540 × 960**. Para um teste rápido, renderize primeiro os quadros em 540 × 960. Nenhum dos comandos usa contas ou serviços externos.

## Corte anterior: v4 cinematográfica

Estudo local, não publicado: **queda pela ponta → contato em macro → abertura invertida → balanço com apoio lateral → aproximação da marca → recuo e assinatura**, em 15 s, 24 fps e formato 9:16. O guarda-chuva começa a se mover imediatamente e desce com mais velocidade visível no primeiro meio segundo. O fundo e piso continuam grafite fosco, com junção discreta. O foco curto isola a ponteira no impacto; uma luz de estúdio se move durante a abertura e revela o tecido e as ferragens. Depois, a câmera se aproxima da impressão “Umbrella” no tecido e volta ao enquadramento amplo antes do letreiro.

O balanço é calculado por código: a copa ganha até cerca de 29° de inclinação, o ponto mais baixo da superfície fica acima do piso pela correção de altura, e a oscilação perde energia até o guarda-chuva voltar a apoiar a ponteira. É uma aproximação visual com geometria da LP, **não uma simulação física de tecido ou corpo rígido**. O som ASMR usa camadas sintéticas locais de queda, ponteira, mecanismo, tecido e atrito leve; é provisório. Nenhuma conta, serviço de renderização ou crédito foi usado.

Reprodução com os assets desta pasta e Blender 4.3+, Python 3, Pillow, NumPy e FFmpeg:

```sh
python3 -m pip install -r motion-001/requirements.txt
python3 motion-001/make_shot_atlas.py
blender --background --factory-startup --python motion-001/render_3d_v4.py -- --out motion-001/v4-frames-1080 --all --width 1080 --height 1920 --samples 32
python3 motion-001/assemble_v4.py --frames motion-001/v4-frames-1080 --out motion-001/v4 --ffmpeg "$(command -v ffmpeg)" --font public/fonts/Manrope.ttf
```

O resultado é `v4/motion-001-v4-1080x1920.mp4`; o montador deriva uma amostra `v4/motion-001-v4-540x960.mp4`. No Windows, use `python` e os caminhos absolutos do Blender e FFmpeg. O atlas da LP permanece intacto: `make_shot_atlas.py` cria a variante da tomada invertida a partir dos pixels originais. Os documentos 01, 02 e 03 continuam na hierarquia de identidade descrita abaixo. Nada é publicado por esses comandos.

## Corte anterior: v3

A v3 estabeleceu **queda pela ponta → contato em macro → abertura invertida → copa inclinada e oscilante → assinatura tipográfica**. A cena mostra piso e parede de estúdio grafite fosco. A v2 ainda não tinha chão legível nem apoio lateral; os cortes em `fall/` e `dist/` foram rejeitados editorialmente.

### Cena 3D v3

| Tempo | Ação |
|---|---|
| 0–5,17 s | O guarda-chuva fechado já se move no primeiro meio segundo e cai com a ponta fina da haste para baixo. A câmera avança até a ponteira; os centímetros finais ocupam um trecho em câmera lenta. |
| 5,17 s | A ponteira toca o piso e tem um ressalto pequeno, amortecido. |
| 5,35–7 s | O mecanismo abre a copa invertida, apoiada na ponteira, com o cabo para cima. A câmera recua para revelar o objeto inteiro. |
| 7–10,5 s | A copa inclina cerca de 30°, a borda toca o piso e o conjunto balança de volta. O giro lento perde energia. |
| 10,45–15 s | Sobe “Umbrella” e, abaixo, “Products that scale, solutions that fit.” em Manrope. |

O modelo articulado, a impressão e o material de tecido vêm da [reconstrução V7 da LP](https://github.com/eduardo-bido/umbrellahq/tree/main/docs/cinematic/cloth-v7/source). Os mapas Terlenka da Poly Haven foram obtidos pelos URLs registrados no manifesto do projeto; os três SHA256 conferem com ele. Para a tomada invertida, `make_shot_atlas.py` cria uma variante local da mesma impressão, apenas girando os pixels do wordmark 180° dentro do mesmo lugar no atlas para que ele seja lido na borda vista pela câmera; o atlas original continua intacto. Essa orientação é um artifício de pré-visualização, a conferir antes de qualquer peça final. A cena de estúdio e a animação de câmera são novas, locais. A queda, o contato e o giro são trajetórias 3D dirigidas por código com amortecimento; **não são uma simulação de corpo rígido validada**. A própria reconstrução V7 continua em revisão e não é um master aprovado. O áudio atual é um rascunho sintético autorizado pelo usuário para sincronização, ainda sem gravação de foley.

Para reproduzir com Blender 4.3+, Python 3, FFmpeg e os arquivos já presentes nesta pasta:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r motion-001/requirements.txt
python3 motion-001/make_shot_atlas.py
blender --background --factory-startup --python motion-001/render_3d.py -- --out motion-001/v3-frames-1080 --all --width 1080 --height 1920 --samples 32
python3 motion-001/assemble_3d.py --frames motion-001/v3-frames-1080 --out motion-001/v3 --ffmpeg "$(command -v ffmpeg)" --font public/fonts/Manrope.ttf
```

O vídeo gerado fica em `v3/motion-001-v3-1080x1920.mp4`, com amostra em `v3/motion-001-v3-540x960.mp4`. Para avaliação rápida, renderize com `--width 540 --height 960 --samples 24`; o arquivo de quadros pode ser montado do mesmo jeito. No Windows, use `python` e o caminho absoluto dos executáveis Blender e FFmpeg. Nenhum comando publica o vídeo nem altera a LP. A versão para postagem exige revisão mobile da articulação, do contato e da leitura da assinatura, além de trocar o som provisório por foley convincente.

## Corte 2D rejeitado

O corte de 12 s em `fall/` usava a tomada horizontal como recorte 2D. A ponta errada tocava o piso e o movimento parecia colagem; foi substituído pela cena 3D acima.

## Estudo anterior

O primeiro corte, em `dist/`, tinha **11,42 s, 24 fps, 1080 × 1920**, com amostra 540 × 960. Usa a tomada CGI que já está na LP e a fonte Manrope do repositório. A trilha de ruído é apenas uma marcação de tempo para avaliar o corte; a versão editorial deve receber foley real gravado localmente.

## Fonte e autoridade visual

O repositório privado `eduardo-bido/umbrellahq` contém `public/experiencia/umbrella-b1/motion-v4.mp4` (274 quadros, 1280 × 720, 24 fps) e `public/fonts/Manrope.ttf`. A LP usa `UmbrellaWordmark` com o texto “Umbrella” em Manrope e um ícone raster de `public/brand`. O vídeo B1 é uma reconstrução CGI própria em revisão: o movimento foi aceito em geral, **o acabamento do tecido e das ferragens não é master aprovado**. As sequências V7/V8 da LP são mais recentes, mas estão armazenadas em pacotes WebP para scroll, não como uma tomada vertical pronta. Fontes: [status da produção](https://github.com/eduardo-bido/umbrellahq/blob/main/docs/cinematic/STATUS.md), [revisão editorial V8](https://github.com/eduardo-bido/umbrellahq/blob/main/docs/cinematic/26-editorial-motion-direction.md), [componente de marca](https://github.com/eduardo-bido/umbrellahq/blob/main/src/components/UmbrellaMark.tsx).

A ordem documental continua: **01 Master Brand Intelligence → 02 Visual Design System → 03 Brand Master Visual**. O 02 rege Manrope, paleta e composição; o 03 referencia wordmark e anatomia; o PDF não fornece vetor ou modelo 3D final. A marca raster selecionada no Brand Bunker não foi copiada para esta pasta. O script usa a implementação tipográfica da LP, **sem alegar que ela é o wordmark master**. A direção A foi selecionada como referência de materialidade, e a revisão posterior retirou as gotas. Fontes: [Visual Bible](https://github.com/eduardo-bido/umbrellahq/blob/main/docs/cinematic/02-visual-bible.md), [manifesto da direção A](https://github.com/eduardo-bido/umbrellahq/blob/main/docs/cinematic/04-asset-manifest.json).

## Conceito do primeiro estudo (rejeitado)

| Tempo | Imagem | Som |
|---|---|---|
| 0–3,2 s | Objeto real da LP em quadro horizontal preservado, isolado no campo grafite; nenhum título. | Fricção discreta de tecido; sem música. |
| 3,2–8,5 s | A própria tomada mostra giro e mecanismo. Sem partículas, neon, zoom falso ou nova geometria. | Dois cliques curtos de mecanismo; ambiente quase silencioso. |
| 9,2–11,42 s | A imagem se apaga; “Umbrella” entra por opacidade e segura até o fim. | Decaimento natural do foley, sem impacto de trailer. |

O quadro da LP é **16:9**. Nesta prova, um recorte suave de 960 × 720 acompanha a passagem do macro para o objeto aberto, sem redesenhar nem deformar o asset. Ainda há bastante espaço vazio no canvas 9:16; o caminho para uma peça final é renderizar **a mesma cena 3D original** com câmera vertical e revisar textura/material, mantendo o rig e a impressão existentes.

## Reprodução do primeiro estudo (rejeitado)

Pré requisitos: checkout local já autorizado do repositório privado, Python 3 e FFmpeg/FFprobe instalados. Homebrew é uma opção local e gratuita: `brew install ffmpeg`. A instalação não exige conta em serviço de vídeo. Se o checkout estiver em `~/Umbrella/umbrellahq`:

```sh
python3 motion-001/render.py --repo ~/Umbrella/umbrellahq --check
python3 motion-001/render.py --repo ~/Umbrella/umbrellahq --out motion-001/dist
```

Para usar áudio gravado em vez da marcação sintética:

```sh
python3 motion-001/render.py --repo ~/Umbrella/umbrellahq --foley ~/Music/umbrella-foley.wav --out motion-001/dist
```

O script falha se a tomada ou a fonte não estiverem no checkout. Não baixa assets e não cria aproximações. O MP4 grande usa H.264/AAC, `yuv420p` e `faststart`; a amostra é derivada dele. Renderiza na pasta local indicada por `--out` e não toca a LP nem a produção. O som de estudo é gerado por código com semente fixa, em volume baixo, para tornar a prova reproduzível. Substituí-lo por fricção e clique captados do objeto é requisito antes de considerar publicação.

## Pesquisa comparativa, 20/10/2026

| Ferramenta/repositório | Licença e Mac | Valor para Motion 001 | Decisão e risco |
|---|---|---|---|
| [FFmpeg](https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md) | LGPL 2.1+ no núcleo; builds com componentes opcionais podem ser GPL. CLI local no Mac. | Composição, fades, áudio e MP4 determinísticos. | **Base mínima.** Sintaxe de filtros exige cuidado; conferir a licença do build usado se for redistribuir binários. |
| [Blender + Python](https://github.com/blender/blender/blob/main/COPYING) | GPL para o software; render local em modo `--background`. O projeto já preserva fonte Blender da cena. | Única opção da lista que reaproveita geometria, câmera, material e luz do guarda-chuva para um novo enquadramento vertical. | **Etapa de acabamento.** Custo de render e ajuste de materiais alto; não reconstruir o objeto do zero. [Fonte V7](https://github.com/eduardo-bido/umbrellahq/blob/main/docs/cinematic/cloth-v7/README.md). |
| [Remotion](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) | Licença própria: grátis para pessoa física, organização sem fins lucrativos e empresa com até 3 funcionários; empresas maiores precisam de licença. Requer Node e macOS 15+ na [documentação atual](https://www.remotion.dev/docs/). | Excelente para controle por quadro, tipografia e múltiplas versões. | **Opcional, não dependência.** O porte jurídico da Umbrella não foi confirmado, então não é a base de custo zero garantido. |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | Skills oficiais para Claude Code e Codex. O repositório não expõe licença clara; há [questão aberta](https://github.com/remotion-dev/skills/issues/28). | Boas práticas para composição, markup e render Remotion. | **Consulta/instalação opcional**, sem copiar para o projeto. Skill não substitui julgamento visual nem dá direitos além da licença do Remotion. |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas/blob/main/LICENSE) | MIT; Node 16+ e editor local. [Exportador FFmpeg](https://github.com/motion-canvas/motion-canvas/blob/main/packages/docs/docs/getting-started/rendering/video.mdx) disponível, ainda descrito como relativamente novo. | Bom para grafismos precisos com TypeScript. | Curva de entrada maior que FFmpeg para esta peça; exportador adiciona manutenção. |
| [GSAP](https://gsap.com/community/standard-license/) | Licença padrão gratuita inclusive comercial, **não open source**, com restrição a ferramentas visuais concorrentes. Já está nas dependências da LP. | Bom para prévia web, easing e revisão de coreografia. | Não é encoder de vídeo; requer captura/exportação adicional. |
| [Three.js](https://github.com/mrdoob/three.js/blob/dev/LICENSE) | MIT; já está nas dependências da LP. | Útil se o objeto mestre estivesse em glTF e fosse preciso câmera interativa. | O modelo oficial não foi localizado; portar a reconstrução Blender para Three só para este reel cria trabalho e diferença de material. |
| [Manim Community](https://github.com/ManimCommunity/manim) | MIT, Python, instalação local com dependências gráficas. | Tipografia e geometria precisa. | Vocabulário visual tende a explicação matemática; pouco ganho para tecido, metal e som. |
| [Liamrjohnston/remotion-motion-graphics-skill](https://github.com/Liamrjohnston/remotion-motion-graphics-skill) | MIT; skill comunitária para agentes. | Bons critérios de legibilidade mobile e assets reais. | Complemento de revisão, não pipeline nem garantia estética; depende de Remotion. |

**Arquitetura escolhida para o corte atual:** geometria, impressão e tecido da reconstrução V7 → Blender/Python para cena 3D vertical → Pillow para tipografia Manrope → FFmpeg para H.264/AAC e amostra mobile. Não há React, Chromium, contas ou serviços de renderização.

### Skills verificadas, somente se Remotion entrar em fase futura

O comando publicado pelo mantenedor é `npx skills add remotion-dev/skills`. Execute dentro de um **projeto de estudo separado** depois de ler os arquivos baixados e confirmar a elegibilidade da licença Remotion. Para uma skill comunitária de critério visual: `npx skills add Liamrjohnston/remotion-motion-graphics-skill`. O [plugin de Claude Code](https://github.com/remotion-dev/claude-code-plugin) e o [plugin de Codex](https://github.com/remotion-dev/codex-plugin) existem, mas a instalação não traz vantagem à arquitetura FFmpeg desta prova. Nenhuma skill foi instalada aqui.

## Revisão no celular

1. Ver a amostra 540 × 960 em tela inteira, com brilho médio e som baixo, primeiro sem fones e depois com fones.
2. No primeiro meio segundo, perceber movimento e reconhecer o guarda-chuva quando a câmera abre; dos 3,3 aos 4,9 s, ver a **ponta da haste** se aproximar do piso. O contato deve ocorrer num único ponto, sem atravessar o chão nem saltar de posição.
3. Entre 5,08 e 5,58 s, sentir a abertura como um estalo, sem deformação brusca. A saída do macro deve revelar a copa inteira; o cabo termina para cima.
4. Entre 5,78 e 10 s, ver a borda tocar o piso, quicar levemente e a oscilação diminuir. O giro não deve parecer uma rotação uniforme de vitrine.
5. Entre 7,16 e 8,12 s, ler a impressão “Umbrella” no tecido; depois, ler o nome e a frase exata em tela pequena, sem invasão da interface do Reels. Reservar pelo menos 250 px no topo e 320 px na base do arquivo 1080 × 1920.
6. Ouvir a ponta tocar, o tecido abrir e os cliques do mecanismo em volume confortável. O áudio sintético atual avalia só ritmo; foley real ainda é necessário para uma peça ASMR final.
7. Comparar quadros representativos com a reconstrução da LP e com os documentos 01/02/03; qualquer divergência de forma, cor ou inscrição volta para revisão, sem promover esta reconstrução a master.

**Estado registrado ao fechar a v5:** os dois assets fornecidos pelo usuário estão em `public/experiencia/umbrella-b1/` e `public/fonts/`, com hashes SHA256 idênticos aos originais. A fonte V7 da reconstrução e a impressão foram recuperadas do repositório privado; os mapas públicos do tecido foram conferidos pelo manifesto. Os cortes em `dist/` e `fall/` foram rejeitados. As v3 e v4 foram renderizadas em 1080 × 1920 e reduzidas para 540 × 960. A v5 foi renderizada em 1080 × 1920 e reduzida para 540 × 960; ambos os MP4s têm 15 s, 24 fps, H.264/AAC e foram decodificados sem erro. O codificador alternativo embutido no Blender também foi testado em 540 × 960, com vídeo e áudio decodificados. O contato/quíque continua uma animação analítica, não uma simulação física de tecido; o apoio da copa deve ser julgado visualmente no celular. A trilha é gerada por código e não foi validada como foley final. Não houve publicação.
