#!/usr/bin/env python3
"""Baixa com segurança um asset de Release pela API REST oficial do GitHub.

O endpoint binário pode responder 200 (stream direto) ou 302 (URL assinada).
O token só é enviado a api.github.com; em redirecionamentos ele nunca é
repassado ao host de armazenamento.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

DEFAULT_API_VERSION = "2026-03-10"
BUFFER_SIZE = 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


class SafeStorageRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        validate_storage_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            # Defesa em profundidade: não encaminhar qualquer credencial.
            redirected.remove_header("Authorization")
        return redirected


def validate_repository(value: str) -> str:
    parts = value.split("/")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    if len(parts) != 2 or any(not p or any(ch not in allowed for ch in p) for p in parts):
        raise ValueError("Repositório inválido; use owner/repo.")
    return value


def validate_storage_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        raise ValueError("O redirecionamento do asset não usa HTTPS.")
    if not (host == "github.com" or host.endswith(".githubusercontent.com")):
        raise ValueError(f"Host de redirecionamento não autorizado: {host or 'vazio'}")
    return value


def request_headers(api_version: str, token: str, accept: str) -> dict[str, str]:
    headers = {
        "Accept": accept,
        "Authorization": f"Bearer {token}",
        "User-Agent": "Radar-TEC1-GitHub-Actions",
        "X-GitHub-Api-Version": api_version,
    }
    return headers


def read_json(url: str, headers: dict[str, str]) -> dict:
    try:
        with urlopen(Request(url, headers=headers), timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"API do GitHub retornou HTTP {response.status}.")
            data = json.load(response)
    except HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", "replace")
        raise RuntimeError(f"API do GitHub retornou HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Falha de rede ao consultar a API do GitHub: {exc.reason}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Resposta inesperada da API do GitHub.")
    return data


def stream_to_file(response: BinaryIO, destination: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with destination.open("wb") as output:
        while True:
            chunk = response.read(BUFFER_SIZE)
            if not chunk:
                break
            output.write(chunk)
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def download_asset(api_url: str, headers: dict[str, str], destination: Path) -> tuple[int, str, int]:
    opener = build_opener(NoRedirect())
    request = Request(api_url, headers=headers)
    try:
        response = opener.open(request, timeout=120)
        status = response.status
    except HTTPError as exc:
        if exc.code != 302:
            detail = exc.read(2048).decode("utf-8", "replace")
            raise RuntimeError(f"Download do asset retornou HTTP {exc.code}: {detail}") from exc
        status = 302
        location = exc.headers.get("Location")
        if not location:
            raise RuntimeError("A resposta 302 do asset não contém Location.") from exc
        validate_storage_url(location)
        storage_opener = build_opener(SafeStorageRedirects())
        storage_request = Request(
            location,
            headers={"Accept": "application/octet-stream", "User-Agent": "Radar-TEC1-GitHub-Actions"},
        )
        try:
            with storage_opener.open(storage_request, timeout=300) as redirected:
                if redirected.status != 200:
                    raise RuntimeError(f"Destino do asset retornou HTTP {redirected.status}.")
                size, sha256 = stream_to_file(redirected, destination)
        except HTTPError as redirect_error:
            detail = redirect_error.read(2048).decode("utf-8", "replace")
            raise RuntimeError(
                f"Destino do asset retornou HTTP {redirect_error.code}: {detail}"
            ) from redirect_error
        return size, sha256, status

    if status != 200:
        response.close()
        raise RuntimeError(f"Resposta inicial inesperada no download do asset: HTTP {status}.")
    try:
        size, sha256 = stream_to_file(response, destination)
    finally:
        response.close()
    return size, sha256, status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-out", type=Path, required=True)
    parser.add_argument("--api-version", default=DEFAULT_API_VERSION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repository = validate_repository(args.repository)
        token = os.environ.get("GH_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GH_TOKEN não foi informado.")

        owner, repo = repository.split("/", 1)
        release_api_url = (
            f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
            f"/releases/tags/{quote(args.tag, safe='')}"
        )
        release = read_json(
            release_api_url,
            request_headers(args.api_version, token, "application/vnd.github+json"),
        )
        if release.get("tag_name") != args.tag:
            raise RuntimeError("A API retornou uma tag diferente da solicitada.")
        if release.get("draft"):
            raise RuntimeError("O Release solicitado ainda está em rascunho.")

        assets = release.get("assets")
        if not isinstance(assets, list):
            raise RuntimeError("A API não retornou a lista de assets do Release.")
        matches = [item for item in assets if item.get("name") == args.asset]
        if len(matches) != 1:
            raise RuntimeError(
                f"Esperado exatamente um asset {args.asset!r}; encontrados: {len(matches)}."
            )
        asset = matches[0]
        if asset.get("state") != "uploaded":
            raise RuntimeError(f"O asset está no estado {asset.get('state')!r}, não 'uploaded'.")
        asset_api_url = str(asset.get("url") or "")
        parsed_api = urlparse(asset_api_url)
        if parsed_api.scheme != "https" or parsed_api.hostname != "api.github.com":
            raise RuntimeError("A URL do asset retornada pela API não é confiável.")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=args.output.parent, delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            size, sha256, initial_status = download_asset(
                asset_api_url,
                request_headers(args.api_version, token, "application/octet-stream"),
                temp_path,
            )
            expected_size = int(asset.get("size") or 0)
            if expected_size <= 0 or size != expected_size:
                raise RuntimeError(
                    f"Tamanho do asset divergente: API={expected_size}, recebido={size}."
                )
            expected_digest = str(asset.get("digest") or "")
            if expected_digest.startswith("sha256:") and sha256 != expected_digest.split(":", 1)[1].lower():
                raise RuntimeError("SHA-256 do asset diverge do digest informado pela API.")
            shutil.move(str(temp_path), args.output)
        finally:
            temp_path.unlink(missing_ok=True)

        metadata = {
            "apiVersion": args.api_version,
            "repository": repository,
            "releaseId": release.get("id"),
            "releaseTag": release.get("tag_name"),
            "releaseApiUrl": release_api_url,
            "releaseHtmlUrl": release.get("html_url"),
            "assetId": asset.get("id"),
            "assetName": asset.get("name"),
            "assetApiUrl": asset_api_url,
            "browserDownloadUrl": asset.get("browser_download_url"),
            "assetState": asset.get("state"),
            "assetContentType": asset.get("content_type"),
            "assetSize": size,
            "assetDigest": asset.get("digest"),
            "assetUpdatedAt": asset.get("updated_at"),
            "downloadInitialStatus": initial_status,
            "sha256": sha256,
        }
        args.metadata_out.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(metadata, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
