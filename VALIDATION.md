# Validação técnica — Dashboard TEC1

## Resultado

**APROVADO para publicação**, condicionado à execução bem-sucedida do workflow no próprio repositório, que é o único ambiente com acesso autenticado ao Release.

## Identidade

- PASSOU — repositório `otaviofelisberto0-creator/Radar_TEC1`.
- PASSOU — competência `2026-07`.
- PASSOU — tag e Release `TEC1-26-07`.
- PASSOU — asset `tec1-26-07.json`.
- PASSOU — URL oficial da API por tag.
- PASSOU — URL oficial de download preservada.
- PASSOU — nenhuma referência ao repositório alternativo.

## API e segurança

- PASSOU — front-end usa `https://api.github.com` com `Accept: application/vnd.github+json` e versão explícita.
- PASSOU — front-end não contém token, PAT ou segredo.
- PASSOU — consulta anônima valida metadados; não baixa o binário de 213 MB.
- PASSOU — indisponibilidade por rede/CORS/rate limit usa somente a entrega same-origin íntegra.
- PASSOU — divergência em resposta válida da API bloqueia o carregamento.
- PASSOU — workflow usa o token automático apenas no runner.
- PASSOU — downloader aceita resposta inicial 200 ou 302.
- PASSOU — token não é encaminhado ao destino do redirect.
- PASSOU — HTTPS e host de armazenamento validados.
- PASSOU — tamanho, SHA-256 e digest oficial comparados.

## Pipeline e integridade

- PASSOU — Python compilado com `py_compile`.
- PASSOU — `dados/manifest.json` analisado como JSON válido.
- PASSOU — workflow analisado como YAML válido.
- PASSOU — scripts JavaScript inline aceitos por `node --check`.
- PASSOU — teste unitário de download 200/302.
- PASSOU — teste end-to-end sintético de build e validação.
- PASSOU — teste end-to-end com o asset real de 223.098.625 bytes.
- PASSOU — SHA-256 real `0e2ef5c7bd50ec89efee399f7d11341bb45cf512b7a448229e1b6419958bb203`.
- PASSOU — 31 partes; nenhuma acima de 8 MiB.
- PASSOU — manifesto de entrega versão 2 com metadados da API.
- PASSOU — reconstrução e comparação lógica de todas as seções.

## Conteúdo preservado

- PASSOU — 13 páginas e 13 links de navegação.
- PASSOU — filtros em cascata e múltipla seleção.
- PASSOU — cálculos TEC1 e funções de normalização.
- PASSOU — gráficos, tabelas e matrizes.
- PASSOU — exportações PDF, Excel, CSV e PNG.
- PASSOU — Semanal, Diária, Gerencial, E-mail, Operacional, EPO, Impacto, Técnico, Conferência e Tempo.
- PASSOU — Página Auxiliar e geração do JSON mensal.

## Verificação obrigatória após o push

1. O job `build` deve registrar resposta inicial 200 ou 302 e concluir a validação do asset.
2. O job `deploy` deve terminar verde.
3. O manifesto de entrega publicado deve ter `versao: 2`.
4. O Dashboard deve confirmar a Release pela API ou informar explicitamente o modo degradado.
5. As 13 páginas devem abrir sem erro e manter filtros e exportações.

## Limitação registrada

O ambiente de validação não conseguiu acessar diretamente o GitHub nem instalar Chromium devido a bloqueios de rede. A chamada real da API e a renderização headless final devem, portanto, ser confirmadas no workflow/site publicado. O pipeline foi testado integralmente com o asset real e os caminhos 200/302 foram testados com servidor controlado.
