name: Publicar Dashboard TEC1

on:
  workflow_dispatch:
  push:
    branches: ["main"]
    paths:
      - "index.html"
      - ".nojekyll"
      - "dados/manifest.json"
      - "tools/download_release_asset.py"
      - "tools/build_release_delivery.py"
      - "tools/validate_delivery.py"
      - ".github/workflows/deploy-tec1-pages.yml"
  release:
    types: [published, released]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages-tec1"
  cancel-in-progress: false

env:
  TEC1_COMPETENCIA: "2026-07"
  TEC1_REPOSITORY: "otaviofelisberto0-creator/Radar_TEC1"
  TEC1_RELEASE_TAG: "TEC1-26-07"
  TEC1_ASSET: "tec1-26-07.json"
  TEC1_API_VERSION: "2026-03-10"
  TEC1_API_RELEASE_URL: "https://api.github.com/repos/otaviofelisberto0-creator/Radar_TEC1/releases/tags/TEC1-26-07"
  TEC1_SOURCE_URL: "https://github.com/otaviofelisberto0-creator/Radar_TEC1/releases/download/TEC1-26-07/tec1-26-07.json"
  TEC1_DELIVERY_DIR: "dados/releases/TEC1-26-07"
  TEC1_DELIVERY_MANIFEST: "tec1-26-07.delivery.json"
  TEC1_PART_BYTES: "8388608"

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Baixar o repositório
        uses: actions/checkout@v4

      - name: Validar configuração fixa da competência
        shell: bash
        run: |
          set -euo pipefail

          python3 - <<'PY'
          import json
          import os
          from pathlib import Path

          manifest_path = Path("dados/manifest.json")
          manifest = json.loads(
              manifest_path.read_text(encoding="utf-8")
          )

          competencia = os.environ["TEC1_COMPETENCIA"]

          itens = [
              item
              for item in manifest.get("arquivos", [])
              if item.get("competencia") == competencia
          ]

          if len(itens) != 1:
              raise SystemExit(
                  f"ERRO: esperado exatamente um item para "
                  f"{competencia}; encontrados: {len(itens)}."
              )

          item = itens[0]

          esperado = {
              "arquivo": os.environ["TEC1_ASSET"],
              "repositorio": os.environ["TEC1_REPOSITORY"],
              "tag": os.environ["TEC1_RELEASE_TAG"],
              "release": os.environ["TEC1_RELEASE_TAG"],
              "sourceUrl": os.environ["TEC1_SOURCE_URL"],
              "tipoEntrega": "github-pages-shards-v1",
              "url": (
                  f"./{os.environ['TEC1_DELIVERY_DIR']}/"
                  f"{os.environ['TEC1_DELIVERY_MANIFEST']}"
              ),
              "ativo": True,
          }

          if manifest.get("competenciaAtual") != competencia:
              raise SystemExit(
                  f"ERRO: competenciaAtual="
                  f"{manifest.get('competenciaAtual')!r}; "
                  f"esperado {competencia!r}."
              )

          divergencias = {
              campo: {
                  "recebido": item.get(campo),
                  "esperado": valor,
              }
              for campo, valor in esperado.items()
              if item.get(campo) != valor
          }

          if divergencias:
              raise SystemExit(
                  "ERRO: configuração fixa divergente: "
                  + json.dumps(
                      divergencias,
                      ensure_ascii=False,
                      sort_keys=True,
                  )
              )

          print("Manifesto principal e variáveis fixas validados.")
          PY

          if LC_ALL=C grep -RIl \
            --exclude-dir=.git \
            --exclude-dir=_site \
            --binary-files=without-match \
            -- 'R-TEC1\.V2' .; then
            echo "Referência proibida encontrada." >&2
            exit 1
          fi

          echo "Nenhuma referência legada encontrada."

      - name: Consultar a API oficial e baixar o asset
        env:
          GH_TOKEN: ${{ github.token }}
        shell: bash
        run: |
          set -euo pipefail

          mkdir -p "$RUNNER_TEMP/tec1-source"

          python3 tools/download_release_asset.py \
            --repository "$TEC1_REPOSITORY" \
            --tag "$TEC1_RELEASE_TAG" \
            --asset "$TEC1_ASSET" \
            --api-version "$TEC1_API_VERSION" \
            --output "$RUNNER_TEMP/tec1-source/$TEC1_ASSET" \
            --metadata-out \
              "$RUNNER_TEMP/tec1-source/release-asset.json"

          test -s \
            "$RUNNER_TEMP/tec1-source/$TEC1_ASSET"

          python3 -m json.tool \
            "$RUNNER_TEMP/tec1-source/$TEC1_ASSET" \
            >/dev/null

          python3 -m json.tool \
            "$RUNNER_TEMP/tec1-source/release-asset.json"

          ls -lh \
            "$RUNNER_TEMP/tec1-source/$TEC1_ASSET"

          sha256sum \
            "$RUNNER_TEMP/tec1-source/$TEC1_ASSET"

      - name: Montar o site e converter o JSON grande em partes
        shell: bash
        run: |
          set -euo pipefail

          rm -rf _site
          mkdir -p _site

          tar -cf - \
            --exclude='./.git' \
            --exclude='./.github' \
            --exclude='./_site' \
            --exclude='./tools' \
            --exclude='./*.zip' \
            --exclude='./SHA256SUMS.txt' \
            --exclude='./dados/releases' \
            . | tar -xf - -C _site

          python3 tools/build_release_delivery.py \
            --input \
              "$RUNNER_TEMP/tec1-source/$TEC1_ASSET" \
            --release-metadata \
              "$RUNNER_TEMP/tec1-source/release-asset.json" \
            --output \
              "_site/$TEC1_DELIVERY_DIR" \
            --repository \
              "$TEC1_REPOSITORY" \
            --tag \
              "$TEC1_RELEASE_TAG" \
            --asset \
              "$TEC1_ASSET" \
            --competencia \
              "$TEC1_COMPETENCIA" \
            --source-url \
              "$TEC1_SOURCE_URL" \
            --manifest-name \
              "$TEC1_DELIVERY_MANIFEST" \
            --max-part-bytes \
              "$TEC1_PART_BYTES"

          touch _site/.nojekyll

      - name: Validar a entrega intermediária
        shell: bash
        run: |
          set -euo pipefail

          python3 tools/validate_delivery.py \
            --site _site \
            --manifest \
              "$TEC1_DELIVERY_DIR/$TEC1_DELIVERY_MANIFEST" \
            --source \
              "$RUNNER_TEMP/tec1-source/$TEC1_ASSET"

          if find _site \
            -type f \
            -size +9M \
            -print -quit | grep -q .; then

            echo \
              "Há arquivo de entrega maior que 9 MiB." \
              >&2

            find _site \
              -type f \
              -size +9M \
              -ls

            exit 1
          fi

      - name: Configurar GitHub Pages
        uses: actions/configure-pages@v5

      - name: Enviar artefato do Pages
        uses: actions/upload-pages-artifact@v4
        with:
          path: _site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}

    runs-on: ubuntu-latest
    needs: build
    timeout-minutes: 10

    steps:
      - name: Publicar no GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
