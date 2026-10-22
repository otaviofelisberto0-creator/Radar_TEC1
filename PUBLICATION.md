# Publicação de ponta a ponta — Dashboard TEC1

## 1. Publicar os arquivos do site

No repositório `otaviofelisberto0-creator/Radar_TEC1`, publique na raiz da branch `main` todo o conteúdo deste pacote, incluindo:

- `index.html`
- `.nojekyll`
- `dados/manifest.json`
- `dados/releases/TEC1-26-07/README.md`
- `.github/workflows/deploy-tec1-pages.yml`
- `tools/download_release_asset.py`
- `tools/build_release_delivery.py`
- `tools/validate_delivery.py`
- documentação e `SHA256SUMS.txt`

Não versione o arquivo de aproximadamente 213 MB na branch. O GitHub bloqueia arquivos comuns acima de 100 MiB; o asset deve permanecer no Release.

## 2. Conferir o Release oficial

Preserve exatamente:

- repositório: `otaviofelisberto0-creator/Radar_TEC1`
- competência: `2026-07`
- tag e Release: `TEC1-26-07`
- asset: `tec1-26-07.json`
- URL da API: `https://api.github.com/repos/otaviofelisberto0-creator/Radar_TEC1/releases/tags/TEC1-26-07`
- URL de download: `https://github.com/otaviofelisberto0-creator/Radar_TEC1/releases/download/TEC1-26-07/tec1-26-07.json`

Mantenha exatamente um asset com esse nome e aguarde o estado `uploaded`. O arquivo continua único e integral no Release.

## 3. Ativar a publicação por GitHub Actions

1. Abra **Settings → Pages**.
2. Em **Build and deployment → Source**, selecione **GitHub Actions**.
3. Salve.

O workflow usa permissões mínimas: `contents: read`, `pages: write` e `id-token: write`. O token automático só existe no runner e não é incluído no site.

## 4. Executar a entrega

O push para `main` inicia **Publicar Dashboard TEC1**. Também é possível abrir:

`https://github.com/otaviofelisberto0-creator/Radar_TEC1/actions/workflows/deploy-tec1-pages.yml`

Clique em **Run workflow** e execute na branch `main`.

O job `build`:

1. valida os identificadores fixos do `dados/manifest.json`;
2. consulta a API REST oficial por tag;
3. localiza exatamente um asset `tec1-26-07.json` no estado `uploaded`;
4. baixa o endpoint oficial do asset com `Accept: application/octet-stream`;
5. aceita resposta inicial `200` ou `302`; em `302`, segue a URL assinada sem encaminhar o token;
6. valida tamanho e digest oficial, quando fornecido;
7. valida a sintaxe do JSON e a competência;
8. divide cada bloco de nível superior em partes de até 8 MiB;
9. calcula SHA-256, tamanho e quantidade de registros de cada parte;
10. gera `dados/releases/TEC1-26-07/tec1-26-07.delivery.json` no artefato do Pages;
11. reconstrói e compara a entrega com o asset original;
12. publica o site.

## 5. Verificar a publicação

Depois que `build` e `deploy` estiverem verdes, verifique:

- Dashboard: `https://otaviofelisberto0-creator.github.io/Radar_TEC1/`
- Manifesto principal: `https://otaviofelisberto0-creator.github.io/Radar_TEC1/dados/manifest.json`
- Manifesto de entrega: `https://otaviofelisberto0-creator.github.io/Radar_TEC1/dados/releases/TEC1-26-07/tec1-26-07.delivery.json`

O manifesto de entrega deve indicar:

- `formato: tec1-json-shards-v1`
- `versao: 2`
- origem com repositório, tag e asset preservados
- `apiReleaseUrl` e `apiAssetUrl` em `api.github.com`
- `downloadStatusInicial` igual a `200` ou `302`
- tamanho e SHA-256 da origem
- partes com tamanho, registros e SHA-256

## 6. Comportamento no navegador

O `index.html` executa duas leituras em paralelo:

1. metadados da Release pela API pública oficial, sem autenticação e sem segredo;
2. manifesto fracionado no mesmo domínio do GitHub Pages.

Uma resposta válida da API é usada para conferir tag, nome, estado, URL, tamanho, ID e digest do asset. Uma divergência bloqueia o carregamento. Se a API não puder ser consultada por rede, CORS ou rate limit, a aplicação registra o aviso e prossegue somente com a entrega same-origin, cuja integridade é validada parte a parte.

O navegador não chama o endpoint binário do asset. Assim, o fluxo analítico não depende de um redirect cross-origin nem de interpretar uma string JSON de aproximadamente 213 MB.

## 7. Fluxo mensal pela Página Auxiliar

1. Abra **Página Auxiliar**.
2. Selecione o CSV e a competência `2026-07`.
3. Converta e baixe `tec1-26-07.json`.
4. Publique ou substitua o asset no Release `TEC1-26-07`.
5. Execute novamente **Publicar Dashboard TEC1**.
6. Aguarde o deploy terminar e recarregue o Dashboard.

Substituir um asset em um Release já existente pode não disparar o evento `release`; por isso, execute o workflow manualmente após a troca.

## 8. Diagnóstico

- **API 404 no front-end:** se o repositório não for público para o visitante, a API não autenticada não verá a Release; o site usa a entrega same-origin já publicada. Nunca coloque token no HTML.
- **API 403/429:** aguarde o rate limit ou recarregue depois; a entrega íntegra permanece disponível.
- **Divergência de tamanho, ID ou digest:** o asset mudou depois do último deploy; execute o workflow novamente.
- **HTTP inicial diferente de 200/302 no workflow:** confirme a tag, o asset, as permissões `contents: read` e o estado do GitHub.
- **Falha em uma parte:** confirme o deploy, limpe o cache e use **Tentar novamente**.
- **SHA-256 divergente:** execute novo deploy e confirme que nenhum arquivo do artefato foi alterado.
- **Manifesto ausente:** confirme que o job `build` terminou antes do `deploy`.
