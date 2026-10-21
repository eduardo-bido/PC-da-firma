# Umbrella Motion 001 — ponto de continuidade

Atualizado em 21/10/2026. Este arquivo preserva o estado do projeto para retomar em outro chat/conta. A v6 ainda NÃO está finalizada nem foi renderizada como vídeo. Não tratar a v5 como aprovada.

## Pedido ativo

Melhorar substancialmente o Reel: zooms anteriores ruins, movimento mecânico, cenário vazio e aparência de jogo. O usuário autoriza pesquisa e trabalho local prolongado, sem contas novas, serviços pagos, créditos de geração, publicação ou alteração de produção. Entrega: MP4 vertical 1080×1920 e prévia540×960, aproximadamente15s, scripts reproduzíveis. Preservar documentos Umbrella01→02→03. A reconstrução da LP não é master aprovado.

O objetivo confirmado é levar a pessoa ao perfil para conhecer a Umbrella. Última direção de texto do usuário: conectar a espera pela queda à capacidade de um site de prender atenção e converter. Copy proposta no chat: “Você esperou a queda.” → “Seu site também precisa prender. E converter.” → “Conheça a Umbrella no perfil.” Preservar a assinatura “Products that scale, solutions that fit.”, sem sobrecarregar a leitura simultânea.

## Ação e direção aprovadas

- Movimento desde o primeiro0,5s. Guarda-chuva fechado cai pela ponta fina da haste por cerca de5s.
- Macro muito próximo da ponteira durante a aproximação final em slow motion; chão legível.
- Contato forte e abertura rápida com som de mecanismo/tecido. Sem música; som provisório autorizado.
- Copa invertida, cabo para cima, grande no quadro. Tombamento de cerca30°, toque no chão e movimento levemente quicado/rotacionado com amortecimento.
- Corte rápido para close da impressão real da marca. Tipografia sobre a cena no final.
- Violeta da marca, estúdio grafite fosco, iluminação mais fotográfica e cenário com cor. Evitar neon futurista e mudanças de lente descontroladas.

## Assets verificados e arquivos anteriores

- `source/geometry.py`, `source/scene.py`, atlas e mapas de tecido vêm da reconstrução V7 do repositório privado `eduardo-bido/umbrellahq`.
- `source/umbrella-print-atlas.png` é a impressão original. A variante `umbrella-print-atlas-inverted-shot.png` gira pixels para a tomada invertida; é artifício documentado de prévia, não master novo.
- `../public/fonts/Manrope.ttf` e `../public/experiencia/umbrella-b1/motion-v4.mp4` correspondem aos arquivos fornecidos pelo usuário.
- `v5/motion-001-v5-1080x1920.mp4` e `v5/motion-001-v5-540x960.mp4` são a última versão entregue, criticada pelo usuário.
- `v5-frames-1080/` contém360quadros. `render_3d_v5.py` e `assemble_v5.py` reproduzem a versão anterior.
- README.md tem histórico, fontes, comandos e comparação de ferramentas. Não sobrescrever fonte proprietária nem produção.

## Trabalho novo já salvo

- `lookdev_v6.py`: scene_setup(width,height,samples,engine='CYCLES') retorna rig,camera,scene. Usa tecido existente, Cycles/OptiX, piso real emz0, fundo curvo, luz direcional e sombra de recorte. `_studio_lights` substitui `_lights` da v5. Não usar posev5 diretamente sem adaptar.
- `diagnostics/look-v6-9.2.png` e `look-v6-1.0.png`: testes de luz, não quadros finais. Avaliação: sombras/material melhoraram, mas enquadramento ainda é emprestado da v5 e precisa ser refeito.
- `diagnostics/lookdev-v6-report.md`: relatório dos testes de luz.
- `motion_v6.py`: novo controlador apply_motion(t,rig), com queda balística remapeada, abertura5,00–5,30s, suporte calculado sobre geometria real e balanço amortecido. Escrito por subagente; ainda precisa revisão/teste integrado. Retorna tip_position,brand_position,matrix,openness,phase e outros dados. Não há câmera neste módulo.
- `RESEARCH_V6.md`: fontes primárias de campanhas e limites da evidência, copy e plano de avaliação. Houve inspeção visual amostral do filme Nike/AirMax no Vimeo, sem download; não houve avaliação auditiva integral.

## Erros concretos encontrados na v5

1. Piso emz=-0,012, ponteira emz0: havia12mm de ar no contato. V6 usa pisoz0 e contato calculado.
2. Câmera interpolava posição e focal em grandes distâncias, causando zoom artificial. Refazer com lentes fixas por plano e cortes motivados.
3. Modelo rígido da copa não permite ponta e borda apoiadas simultaneamente a30° sem deformação. Aceitar transferência plausível de apoio e pequena elevação da ponta durante o tombamento; não alegar simulação física completa.
4. Excesso de fontes/luz de preenchimento achatava tecido e chão. Cycles GPU local é viável.

## Próximos passos necessários

1. Revisar/testar motion_v6.py: trajetória, apoios, ausência de penetração, amplitudes de balanço e legibilidade da marca.
2. Criar render_3d_v6.py com planos de lente fixa. Esboço ainda não implementado:0–1,25s produto fechado grande e diagonal com movimento imediato;1,25–3,35s queda com piso/sombra;3,35–5,00s macro de contato;5,00–6,8s abertura rápida e primeiro balanço;6,8–8,5s close da impressão;8,5–15s hero e copy/CTA.
3. Dar atenção à câmera macro: t3,35 ponta~0,144m; t4,0~0,065m; t4,9 contato. Evitar perseguir a ponta a ponto de esconder sua aproximação do chão.
4. Implementar motion blur real dos transforms com keyframes quando viável. O rig atual atualiza mesh/curvas por código; não presumir que ativar motion blur sozinho captura a deformação da abertura.
5. Criar assemble_v6.py com copy em etapas, Manrope, tagline exata e CTA de perfil. Sincronizar áudio provisório aos novos tempos, sem prometer foley autêntico.
6. Renderizar testes de quadros, rever; depois vídeo reduzido completo e revisar temporalmente. Só então1080×1920 e preview final, decodificar ambos e atualizar documentação.

## Ambiente local confirmado

Pasta: `C:\Users\eduardo.bido\Documents\ChatGPT\Umbrella Group`.

- Blender4.3.2: `C:\Program Files\Blender Foundation\Blender 4.3\blender.exe`.
- GPU NVIDIA RTX3060Ti8GB. CyclesOptiX32samples540×960: cerca2,3s por quadro após inicialização no teste. Não há render longo ativo neste checkpoint.
- Python3.12: comando `python`; NumPy e Pillow já instalados.
- FFmpeg: `C:\Program Files\ShareX\ffmpeg.exe` (não está no PATH).
- Scripts de montagem usam FFmpeg/Pillow. Existe encoder alternativo embutido no Blender testado em540×960.

Três subagentes colaboraram nesta rodada, mas terminaram com aviso de limite de uso depois de salvar seus módulos/documentos. Não há motivo para comprar créditos. A revisão e integração dos módulos ainda são responsabilidade do agente que retomar.

## Como retomar em um chat novo

Abra esta mesma pasta no aplicativo desktop, permita seu acesso e peça: “Leia motion-001/CONTINUAR_AQUI.md, confira os arquivos existentes e continue a v6 do Motion001. Não refaça a v5 nem considere a tarefa concluída.”

O chat original local chama-se “Criar prova de conceito Motion 001”, id01a1591d-7920-73d0-84d0-32fb7e7f36c3. Um novo chat precisa deste contexto; não presumir que trocar de conta transfere histórico ou acesso aos conectores.
