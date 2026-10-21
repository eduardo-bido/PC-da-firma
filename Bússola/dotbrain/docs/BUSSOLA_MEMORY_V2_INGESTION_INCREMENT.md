# Memory Engine V2: primeiro incremento de ingestão

Esta implementação acrescenta metadados V2 opcionais ao `capture_thought`. O texto original continua em `thoughts.content`; o registro V2 fica em `thoughts.doc_map.bussola.episode_v2`. Nenhuma tabela ou dado histórico é alterado.

## Contrato seguro

- O chamador informa um `request_id` UUID estável por mensagem ou episódio. Repetir a mesma chamada devolve o pensamento anterior; mudar texto, modo ou metadados para o mesmo ID falha.
- `source_reference` identifica a mensagem na origem, sem presumir que o texto foi dito diretamente pelo usuário. Neste primeiro incremento, a origem é `chatgpt` e a referência é fornecida pelo chamador.
- `occurred_at` preserva a precisão informada: timestamp ISO com fuso para `day`, `YYYY-MM` para `month`, `YYYY` para `year`, ou `null` para `unknown`. `created_at` continua sendo a data de gravação do banco.
- `knowledge_kind`, `epistemic_status` e `temporal_status` qualificam o episódio bruto. `promotion_status: raw_only` informa que nenhuma claim ou sinapse foi validada.
- O caminho V2 aceita apenas `privacy: standard` e `processing_mode: semantic_only`. Dados restritos exigem segmentação e controle de acesso antes da ingestão. A indexação leve gera embeddings e não executa extração de tarefas, agenda ou finanças.
- `search_memory` devolve a referência e os marcadores V2 junto aos trechos originais, quando presentes. Episódios antigos continuam legíveis, sem metadados inventados.

## Validação híbrida

Decisão confirmada em 20/10/2026: perguntar imediatamente apenas sobre decisões importantes; agrupar dúvidas menores para revisão em lote. O estágio futuro de candidatos deve guardar fonte, data, hipótese e motivo de revisão sem promover silenciosamente sinapses incertas. Este incremento só grava memória bruta qualificada; a fila de revisão e a promoção ao grafo ainda não estão implementadas.

## Limites e próximos passos

O `request_id` protege retries da mesma captura. Ainda não há unicidade por `source_reference` entre IDs diferentes nem importação em lote; o chamador deve manter o mapeamento estável. Não iniciar backfill antes de staging, dedupe por fonte e revisão de privacidade. O modo `full` legado continua fora do caminho V2 e pode gerar sugestões pelo extrator atual; não usá-lo para importações.
