# TEC1 — Julho/2026

Release mensal oficial do Dashboard TEC1.

## Asset obrigatório

- `tec1-26-07.json`

O Dashboard consulta os metadados desta Release pela API REST oficial do GitHub. O workflow **Publicar Dashboard TEC1** baixa o asset pelo endpoint oficial, trata resposta HTTP 200 ou 302, valida tamanho/digest, gera a entrega fracionada same-origin e publica o site no GitHub Pages.

O navegador não transfere diretamente o arquivo monolítico de aproximadamente 213 MB e não contém token ou segredo.
