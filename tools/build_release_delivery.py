#!/usr/bin/env python3
"""Converte um JSON mensal TEC1 em partes pequenas para entrega pelo GitHub Pages.

O Release continua sendo a fonte oficial. Este utilitário é executado no GitHub
Actions depois que a API REST oficial baixa e valida o asset. O utilitário
materializa fragmentos estáticos na mesma origem do Dashboard, evitando que o
navegador transfira e interprete um JSON monolítico de aproximadamente 213 MB.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

FORMAT = "tec1-json-shards-v1"
REQUIRED_ARRAYS = ("dados", "tecnicos", "operacional")


def compact(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_part(output_dir: Path, name: str, data: bytes, count: int) -> dict[str, Any]:
    path = output_dir / name
    path.write_bytes(data)
    return {
        "arquivo": name,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "registros": count,
    }


def write_array_parts(output_dir: Path, section: str, rows: list[Any], max_bytes: int) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    current: list[bytes] = []
    current_size = 2  # [ ]

    def flush() -> None:
        nonlocal current, current_size
        if not current:
            return
        payload = b"[" + b",".join(current) + b"]"
        name = f"{section}-{len(parts):04d}.json"
        parts.append(write_part(output_dir, name, payload, len(current)))
        current = []
        current_size = 2

    for row in rows:
        encoded = compact(row)
        projected = current_size + len(encoded) + (1 if current else 0)
        if current and projected > max_bytes:
            flush()
        current.append(encoded)
        current_size += len(encoded) + (1 if len(current) > 1 else 0)
    flush()

    if not parts:
        parts.append(write_part(output_dir, f"{section}-0000.json", b"[]", 0))
    return parts


def build(args: argparse.Namespace) -> dict[str, Any]:
    source = args.input.resolve()
    output_dir = args.output.resolve()
    release_metadata_path = args.release_metadata.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Asset não encontrado: {source}")
    if not release_metadata_path.is_file():
        raise FileNotFoundError(f"Metadados da API do GitHub não encontrados: {release_metadata_path}")
    if args.max_part_bytes < 1024:
        raise ValueError("max-part-bytes deve ser pelo menos 1024")

    release_metadata = json.loads(release_metadata_path.read_text(encoding="utf-8"))
    required_release_values = {
        "repository": args.repository,
        "releaseTag": args.tag,
        "assetName": args.asset,
        "browserDownloadUrl": args.source_url,
        "assetState": "uploaded",
    }
    for field, expected in required_release_values.items():
        if str(release_metadata.get(field) or "") != str(expected):
            raise ValueError(
                f"Metadado da API divergente em {field}: "
                f"{release_metadata.get(field)!r} em vez de {expected!r}."
            )

    source_bytes = source.read_bytes()
    source_sha = sha256_bytes(source_bytes)
    if int(release_metadata.get("assetSize") or 0) != len(source_bytes):
        raise ValueError("Tamanho do arquivo difere do tamanho validado pela API do GitHub.")
    if str(release_metadata.get("sha256") or "").lower() != source_sha:
        raise ValueError("SHA-256 do arquivo difere do valor validado no download pela API.")
    api_digest = str(release_metadata.get("assetDigest") or "")
    if api_digest.startswith("sha256:") and api_digest.split(":", 1)[1].lower() != source_sha:
        raise ValueError("Digest oficial do asset difere do SHA-256 calculado.")
    try:
        bundle = json.loads(source_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"O asset {source.name} não contém JSON UTF-8 válido: {exc}") from exc
    finally:
        del source_bytes

    if not isinstance(bundle, dict):
        raise ValueError("O JSON mensal deve ser um objeto no nível superior.")
    for field in REQUIRED_ARRAYS:
        if not isinstance(bundle.get(field), list):
            raise ValueError(f'O bloco obrigatório "{field}" deve ser uma lista.')

    metadata = bundle.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError('O bloco obrigatório "metadata" deve ser um objeto.')
    competence = str(metadata.get("competencia") or args.competencia)
    if competence != args.competencia:
        raise ValueError(f"Competência do JSON ({competence}) difere da esperada ({args.competencia}).")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sections: dict[str, Any] = {}
    total_delivery_bytes = 0
    total_parts = 0

    for name, value in bundle.items():
        if isinstance(value, list):
            parts = write_array_parts(output_dir, name, value, args.max_part_bytes)
            descriptor = {
                "tipo": "array",
                "registros": len(value),
                "partes": parts,
            }
        else:
            payload = compact(value)
            part = write_part(output_dir, f"{name}.json", payload, 1)
            descriptor = {
                "tipo": "valor",
                "partes": [part],
            }
        descriptor["bytes"] = sum(p["bytes"] for p in descriptor["partes"])
        sections[name] = descriptor
        total_delivery_bytes += descriptor["bytes"]
        total_parts += len(descriptor["partes"])

    delivery = {
        "formato": FORMAT,
        "versao": 2,
        "competencia": args.competencia,
        "geradoEm": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "origem": {
            "repositorio": args.repository,
            "tag": args.tag,
            "release": args.tag,
            "asset": args.asset,
            "url": args.source_url,
            "apiVersion": release_metadata.get("apiVersion"),
            "apiReleaseUrl": release_metadata.get("releaseApiUrl"),
            "apiAssetUrl": release_metadata.get("assetApiUrl"),
            "releaseId": release_metadata.get("releaseId"),
            "assetId": release_metadata.get("assetId"),
            "assetUpdatedAt": release_metadata.get("assetUpdatedAt"),
            "assetDigest": release_metadata.get("assetDigest"),
            "downloadStatusInicial": release_metadata.get("downloadInitialStatus"),
            "bytes": source.stat().st_size,
            "sha256": source_sha,
        },
        "entrega": {
            "mesmaOrigem": True,
            "corsNecessario": False,
            "maximoBytesPorParte": args.max_part_bytes,
            "totalBytes": total_delivery_bytes,
            "totalPartes": total_parts,
        },
        "secoes": sections,
    }
    manifest_path = output_dir / args.manifest_name
    manifest_path.write_bytes(json.dumps(delivery, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    return delivery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--competencia", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--release-metadata", type=Path, required=True)
    parser.add_argument("--manifest-name", default="tec1-26-07.delivery.json")
    parser.add_argument("--max-part-bytes", type=int, default=8 * 1024 * 1024)
    return parser.parse_args()


def main() -> int:
    try:
        delivery = build(parse_args())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "formato": delivery["formato"],
        "competencia": delivery["competencia"],
        "partes": delivery["entrega"]["totalPartes"],
        "bytes": delivery["entrega"]["totalBytes"],
        "sha256Origem": delivery["origem"]["sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
