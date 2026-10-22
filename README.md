# Dashboard TEC1 — solução final com API oficial e entrega same-origin

Aplicação estática pronta para publicação no repositório **otaviofelisberto0-creator/Radar_TEC1**.

## Identidade preservada

- Repositório: `otaviofelisberto0-creator/Radar_TEC1`
- GitHub Pages: `https://otaviofelisberto0-creator.github.io/Radar_TEC1/`
- Competência: `2026-07`
- Tag e Release: `TEC1-26-07`
- Asset oficial: `tec1-26-07.json`
- URL da API: `https://api.github.com/repos/otaviofelisberto0-creator/Radar_TEC1/releases/tags/TEC1-26-07`
- URL de download registrada: `https://github.com/otaviofelisberto0-creator/Radar_TEC1/releases/download/TEC1-26-07/tec1-26-07.json`

## Decisão técnica

A API REST oficial do GitHub passou a ser usada em dois pontos, com responsabilidades diferentes:

1. **JavaScript no front-end:** consulta os metadados da Release por tag, localiza exatamente um asset `tec1-26-07.json` e valida tag, estado `uploaded`, tamanho, URL, ID e digest quando disponível.
2. **GitHub Actions:** usa o token interno de leitura do repositório para consultar a mesma API e baixar o binário pelo endpoint oficial do asset. O downloader aceita os dois comportamentos documentados: HTTP `200` com stream direto ou HTTP `302` com URL assinada.

O navegador **não baixa diretamente** o JSON monolítico de aproximadamente 213 MB. Esse download seria mais sujeito a CORS/redirecionamentos e produziria um pico alto de memória durante `text()`/`JSON.parse()`. O workflow valida o arquivo, divide cada seção em partes de no máximo 8 MiB e publica as partes na mesma origem do Dashboard.

O front-end carrega as partes sequencialmente, valida tamanho e SHA-256 e só então interpreta cada fragmento. Se a API pública estiver temporariamente indisponível por rede, CORS ou rate limit, o Dashboard continua usando a entrega same-origin assinada por hashes; qualquer divergência encontrada em uma resposta válida da API bloqueia o carregamento e exige novo deploy.

Nenhum token, PAT ou segredo é colocado no HTML.

## Arquivos principais

- `index.html` — Dashboard completo, consulta da API oficial e carregador fracionado.
- `dados/manifest.json` — fixa repositório, tag, asset, versão da API e manifesto same-origin.
- `.github/workflows/deploy-tec1-pages.yml` — consulta a API, baixa o asset, gera e publica o site.
- `tools/download_release_asset.py` — trata download oficial HTTP 200/302 sem vazar o token em redirecionamentos.
- `tools/build_release_delivery.py` — converte o JSON mensal em fragmentos e incorpora os metadados validados da API.
- `tools/validate_delivery.py` — valida hashes, contagens, origem e equivalência com o asset.
- `PUBLICATION.md` — procedimento completo de publicação e operação.

## Publicação resumida

1. Publique todo o conteúdo desta pasta na raiz da branch `main` do repositório preservado.
2. Confirme que o Release `TEC1-26-07` contém exatamente um asset `tec1-26-07.json` no estado `uploaded`.
3. Em **Settings → Pages**, selecione **GitHub Actions** como origem.
4. Faça push para `main` ou execute manualmente **Publicar Dashboard TEC1**.
5. Aguarde os jobs `build` e `deploy` concluírem.
6. Valide o Dashboard e os dois manifestos listados em `PUBLICATION.md`.

## Conteúdo funcional preservado

As 13 páginas, a navegação SPA, filtros em cascata e múltipla seleção, cálculos TEC1, gráficos, tabelas, exportações PDF/Excel/CSV/PNG, análises Semanal, Diária, Gerencial, E-mail, Operacional, EPO, Impacto, Técnico, Conferência, Tempo e a Página Auxiliar permanecem no mesmo `index.html`.
