# Revisão V7 — 22/10/2026

## Verificado

- Dois MP4s: 1080×1920 e 540×960, 20,0417 s, 481 quadros a 24 fps, H.264/AAC e Rec.709. Ambos decodificados por inteiro sem erros; hashes em `verification.json`.
- Composição HyperFrames: lint, runtime, layout e contraste sem erros ou avisos nas amostras do `../hyperframes-v7/check-report.json`. O teste automático de movimento não foi ativado; não inferir aprovação de fluidez desse relatório.
- Quadros exportados inspecionados em 0; 0,5; 2,5; 4,5; 5; 5,42; 5,7; 7; 10; 11,5; 14; 15,5; 18,5 e 20 s, reunidos em `contact-sheet.png`. Contato na ponteira, abertura, texto e fechamento presentes. Nenhuma legenda cobre o objeto nos quadros observados.
- Prévia MP4 reproduzida no navegador até o final; observados início, legenda após a abertura, contato por busca e tela final. Isso não equivale a observação contínua de cada quadro nem audição pelo agente.
- Voz Thalita escolhida pelo usuário após duas vozes locais rejeitadas e comparação Edge. Geração online gratuita sem conta foi explicitamente autorizada. Arquivo WAV tem silêncio inicial até aproximadamente 5,856 s e fala até 15,431 s. Convite permanece até o final.
- Análise de áudio do MP4: integrado **−14,57 LUFS**, true peak **−2,10 dBTP**, LRA **8,10 LU**. Não foi aplicado o áudio de saída da análise; valores são medidos no arquivo entregue. Pico abaixo de 0 dBTP, sem evidência de clipping pela medição.
- Não houve publicação, conta nova, cobrança, créditos ou alteração da LP.

## Problemas e limites

- Tecido fechado ainda rígido/estriado na reconstrução existente. Principal limite do realismo. Não foi encontrado um master 3D proprietário para substituir isso com fidelidade.
- O cenário tem uma faixa cinza na margem esquerda em alguns quadros do plano aberto; mantida como limite desta versão, sem disfarçar o problema com novo enquadramento digital.
- Física dirigida por código, sem tecido com auto-colisão ou massas medidas. Não chamar de filmagem real.

## Não inspecionado / aprovação pendente

- Agente não ouviu a mixagem final. Escolha da amostra pelo usuário não comprova dicção de toda a fala, equilíbrio perceptivo ou sincronismo auditivo final.
- Não houve aprovação do Reel completo pelo usuário, teste em celular físico ou preview real do Instagram. Conferir leitura a 360 px, com/sem som, interface e pronúncia Umbrella antes de postar.
- Não há métricas de retenção/conversão. Referências consultadas não comprovam resultado desta peça.

Identidade: Umbrella 01 → 02 → 03 permanece superior. A impressão e a reconstrução não foram promovidas a master.
