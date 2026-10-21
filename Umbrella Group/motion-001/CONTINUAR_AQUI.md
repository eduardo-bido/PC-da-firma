# Umbrella Motion 001 — estado atual

Atualizado em 21/10/2026. **V6 exportada e verificada**: 15 segundos, 24 fps, 360 quadros, H.264/AAC estéreo e Rec.709. Os dois MP4s foram decodificados por inteiro sem erros. Esta é uma iteração da reconstrução da LP, não um master de identidade aprovado.

## Entregas

- `v6/motion-001-v6-1080x1920.mp4`: vídeo vertical em resolução cheia.
- `v6/motion-001-v6-540x960.mp4`: prévia derivada do arquivo grande.
- `v6/hero-frame.png` e `v6/contact-sheet.png`: referências de revisão.
- `v6/sound-mix.wav`: mixagem local.
- `v6/render-report.json`: parâmetros da cena.
- `v6/verification.json`: duração, dimensões, quadros e SHA256 dos vídeos.

O pedido foi continuar o desenvolvimento neste computador e enviar o resultado ao repositório `eduardo-bido/PC-da-firma`, dentro de **Umbrella Group**. O usuário fará eventual publicação do Reel. Não houve publicação no Instagram ou alteração da LP.

## Conceito e mensagem

Queda pela ponta fina da haste por cerca de 5 s, macro do contato, abertura rápida, guarda-chuva invertido com cabo para cima, balanço com transferência de apoio, corte para a impressão e fechamento com CTA ao perfil.

Texto em etapas:

1. “Você esperou a queda.”
2. “Seu site também precisa prender.”
3. “E converter.”
4. “Umbrella” / “Products that scale, solutions that fit.”
5. “Conheça a Umbrella no perfil”

O objetivo é visita ao perfil. Retenção e conversão ainda não foram medidas. A pesquisa e seus limites estão em `RESEARCH_V6.md`.

## Implementação vigente

- `render_3d_v6.py`: seis tomadas com lentes fixas; cortes nos quadros 0, 30, 80, 120, 164 e 204; blur de transformação e render por intervalos.
- `motion_v6.py`: queda balística em relógio de slow motion; contato 4,90 s; abertura 5,00–5,30 s; inclinação máxima de 29,76° e apoio na geometria existente. O foco da marca usa a posição da impressão na superfície do tecido.
- `cloth_pose_v6.py`: quatro pregas por painel fechado, pelo solver original de área. Estado aberto, UV e impressão preservados.
- `lookdev_v6.py`: Cycles, detecção de GPU, key lateral, fundo ameixa e recorte âmbar. Luz do fundo vinculada apenas ao cenário. OptiX também faz o denoise quando disponível.
- `assemble_v6.py`: Manrope, mensagem em etapas, CTA, áudio e MP4s.
- `verify_v6.py`: valida os vídeos por decodificação integral, sem ffprobe.
- `review-v6.html`: revisão local por tomada e avanço de um quadro.

## Assets e identidade

Preservar **Umbrella 01 → 02 → 03**. Os documentos completos não estão nesta cópia; o README registra referências ao repositório original privado `eduardo-bido/umbrellahq`.

`source/geometry.py`, `source/scene.py`, impressão e mapas Terlenka são os assets da reconstrução V7 da LP. `public/fonts/Manrope.ttf` e `public/experiencia/umbrella-b1/motion-v4.mp4` correspondem aos arquivos fornecidos pelo usuário. Não substituir um asset ausente por aproximação nem tratar a reconstrução como master.

O atlas invertido é uma variante de orientação da impressão para a tomada e permanece documentado como artifício de prévia. A fonte original está preservada.

O áudio mistura uma abertura real CC0 por **bewareofkites20**, obtida da prévia pública do Freesound, com contatos e texturas procedurais locais. MP3, WAV e licença estão em `source/audio/`. Não houve conta nova, serviço pago ou geração com créditos. Os contatos não são gravação deste objeto proprietário.

## Limites e revisão futura

A abertura e o apoio são dirigidos por código; não há simulação de tecido com auto-colisão nem massas medidas. A revisão incluiu reprodução reduzida e inspeção de contato, abertura, impressão e tipografia. Métricas automáticas verificam arquivos, não comprovam qualidade estética ou conversão.

As versões anteriores continuam como histórico. A v5 foi criticada por zooms artificiais, movimento mecânico, cenário vazio e pouca clareza comercial. Não retomá-la como aprovada.

## Reproduzir ou continuar em outra máquina

Abra **Umbrella Group** no checkout de `PC-da-firma`. Leia a seção V6 do README para render, montagem e verificação. Detecte os executáveis desta máquina; não reutilize caminhos absolutos do Windows em um Mac.

Nesta entrega: Blender 4.3.2, RTX 3060 Ti 8 GB, Python 3.12, NumPy/Pillow e FFmpeg do ShareX. O render final usa 24 amostras com denoise, 1080×1920 e todos os 360 quadros. Os quadros intermediários novos ficam fora do Git e podem ser recriados.

Para uma nova iteração, parta dos MP4s V6 e das correções concretas do usuário. Preserve produção local gratuita, assets e hierarquia de identidade; obtenha autorização própria antes de publicar em redes sociais.
