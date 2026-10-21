# Testes do front-end e da entrega — solução final TEC1

Escopo canônico: repositório `otaviofelisberto0-creator/Radar_TEC1`, GitHub Pages `https://otaviofelisberto0-creator.github.io/Radar_TEC1/`, Release `TEC1-26-07` e asset `tec1-26-07.json`.

## Asset real de aproximadamente 213 MB

O asset oficial foi reconstruído byte a byte a partir da entrega previamente validada e conferido contra os metadados da origem:

- PASSOU — tamanho: `223.098.625` bytes.
- PASSOU — SHA-256: `0e2ef5c7bd50ec89efee399f7d11341bb45cf512b7a448229e1b6419958bb203`.
- PASSOU — reconstrução idêntica à origem.
- PASSOU — processamento completo pela nova versão de `build_release_delivery.py`.
- PASSOU — validação completa pela nova versão de `validate_delivery.py`.
- PASSOU — manifesto de entrega versão 2.
- PASSOU — 31 partes, maior parte com exatamente `8.388.608` bytes.
- PASSOU — 6.380 registros em `dados`, 2.288 em `tecnicos` e 129.987 em `operacional`.

Tempos observados neste ambiente: 15,740 s para geração e 18,778 s para validação integral.

## Respostas 200 e 302

Testes com servidor HTTP controlado:

- PASSOU — resposta inicial `200` com stream direto.
- PASSOU — resposta inicial `302`, leitura de `Location` e segundo download.
- PASSOU — tamanho e SHA-256 do conteúdo iguais nos dois caminhos.
- PASSOU — rejeição de HTTP e de host fora da lista segura.
- PASSOU — o fluxo redirecionado não reutiliza o cabeçalho `Authorization`.

## JavaScript da API oficial

Testes isolados do código real extraído do `index.html`:

- PASSOU — montagem da URL oficial por repositório e tag.
- PASSOU — validação de tag, asset, estado, tamanho, ID, URL e digest.
- PASSOU — resposta válida da API libera a entrega correspondente.
- PASSOU — falha de rede/CORS ativa o modo degradado sem token e sem download direto do asset.
- PASSOU — divergência de tamanho/digest bloqueia a entrega.
- PASSOU — os quatro blocos de JavaScript inline foram aceitos por `node --check`.

## Preservação funcional estática

Comparação entre o `index.html` de origem e o final:

- PASSOU — 13 páginas antes e depois.
- PASSOU — 13 links de navegação antes e depois.
- PASSOU — 8 filtros principais antes e depois.
- PASSOU — 18 controles de exportação PDF antes e depois.
- PASSOU — 9 controles de exportação Excel antes e depois.
- PASSOU — 11 elementos `canvas` antes e depois.
- PASSOU — 15 tabelas declaradas antes e depois.
- PASSOU — Página Auxiliar TEC1 preservada.

## Carregamento same-origin por HTTP

Teste de integração com o site final servido por HTTP local:

- PASSOU — leitura de `dados/manifest.json` e seleção da competência ativa `2026-07`.
- PASSOU — leitura do manifesto de entrega versão 2.
- PASSOU — download e validação de 31 partes, totalizando `223.098.583` bytes.
- PASSOU — reconstrução de 6.380 registros em `dados`, 2.288 em `tecnicos` e 129.987 em `operacional`.
- PASSOU — presença das 13 páginas, inclusive a Página Auxiliar.

## Limite do ambiente de teste

A instalação do Chromium para uma nova execução headless foi bloqueada pela política de rede do ambiente de validação. Por isso, não foi repetida aqui uma renderização visual automatizada. A sintaxe JavaScript, a lógica da API/fallback, o pipeline completo com o asset real, o carregamento same-origin por HTTP e a preservação estrutural foram validados; as páginas, análises e componentes visuais não foram reescritos.
