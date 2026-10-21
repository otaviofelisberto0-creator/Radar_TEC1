# Publicação TEC1 — TEC1-26-07

## 1. Publicar o site

No repositório `otaviofelisberto0-creator/R-TEC1.V2`, publique na raiz:

- `index.html`
- `.nojekyll`
- `dados/manifest.json`

Ative o GitHub Pages para a branch/pasta em que esses arquivos foram publicados. Endereço esperado:

`https://otaviofelisberto0-creator.github.io/R-TEC1.V2/`

## 2. Gerar o JSON mensal

1. Acesse `#admin` no dashboard.
2. Selecione o CSV.
3. Mantenha a competência `2026-07`.
4. Clique em **1. Converter CSV para JSON**.
5. Confira as contagens e mensagens de validação.
6. Clique em **2. Baixar arquivo JSON**.

O nome gerado deve ser `tec1-26-07.json`. Linhas de outras competências não entram no arquivo mensal.

## 3. Criar a publicação mensal

1. Abra `https://github.com/otaviofelisberto0-creator/R-TEC1.V2/releases/new?tag=TEC1-26-07&title=TEC1-26-07`.
2. Confirme a tag `TEC1-26-07`.
3. Use o título `TEC1-26-07`.
4. Anexe `tec1-26-07.json`.
5. Publique o Release.

## 4. Conferir o carregamento

A URL esperada é:

`https://github.com/otaviofelisberto0-creator/R-TEC1.V2/releases/download/TEC1-26-07/tec1-26-07.json`

O `dados/manifest.json` já aponta diretamente para essa URL. Ao abrir o GitHub Pages, confirme:

- competência `Julho/2026`;
- preenchimento de **Última atualização** e **Dados até**;
- painel de carregamento concluído;
- indicadores, gráficos e tabelas com dados;
- páginas Operacional, Resultado por EPO, Impacto, Resultado por Técnico e Conferência alimentadas pelo bloco `operacional`;
- exportações em PDF, Excel, CSV e PNG conforme cada página.

Se o asset ainda não estiver publicado, o painel informa a falha e permite **Tentar novamente** ou **Ver detalhes**.
