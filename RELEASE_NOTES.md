# Notas da solução final — API oficial + entrega segura

## Preservado

- Repositório `otaviofelisberto0-creator/Radar_TEC1`.
- Release/tag `TEC1-26-07` e asset `tec1-26-07.json`.
- Competência `2026-07`.
- 13 páginas e navegação SPA.
- Filtros em cascata e múltipla seleção.
- Cálculos TEC1, gráficos, tabelas e exportações.
- Análises Semanal, Diária, Gerencial, E-mail, Operacional, EPO, Impacto, Técnico, Conferência e Tempo.
- Página Auxiliar TEC1 e geração do JSON mensal.

## Ajustado

- O front-end agora consulta a Release por tag na API REST oficial do GitHub.
- A resposta da API valida o asset por nome, estado, URL, tamanho, ID e digest.
- A consulta do front-end é anônima e nunca expõe token.
- Indisponibilidade de API, CORS ou rate limit não invalida a entrega same-origin já verificada; divergências reais bloqueiam o carregamento.
- O GitHub Actions deixou de depender do comando `gh release download` e passou a usar diretamente os endpoints oficiais da API.
- Corrigido o cabeçalho `Authorization` do downloader para usar o token automático no formato `Bearer`, restrito a `api.github.com`.
- O downloader trata explicitamente resposta inicial HTTP `200` ou `302`.
- Em `302`, o token não é encaminhado para a URL assinada do armazenamento.
- Metadados oficiais do Release e do asset são incorporados ao manifesto de entrega versão 2.
- O JSON de aproximadamente 213 MB permanece no Release e não é transferido diretamente pelo navegador.
- As partes same-origin continuam limitadas a 8 MiB, com tamanho, contagem e SHA-256 individuais.
- O carregamento continua sequencial e incremental, com tentativas, timeout e progresso.

## Segurança

- Segredos restritos ao runner do GitHub Actions.
- Hosts de redirecionamento validados e HTTPS obrigatório.
- Token removido em qualquer redirecionamento.
- Repositório, tag, asset e URLs fixos validados no workflow e no front-end.
- Digest oficial comparado ao SHA-256 calculado quando disponível.
- Cache das partes versionado pelo SHA-256 da origem.
