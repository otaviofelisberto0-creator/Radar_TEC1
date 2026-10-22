#!/usr/bin/env python3
"""Gera uma entrega TEC1 fracionada para publicação no GitHub Pages."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

FORMAT = "tec1-json-shards-v1"
VERSION = 2


def encode_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--release-metadata", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repository", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--asset", required=True)
    p.add_argument("--competencia", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--manifest-name", required=True)
    p.add_argument("--max-part-bytes", type=int, default=8 * 1024 * 1024)
    return p.parse_args()


def split_array(rows: list[Any], max_bytes: int) -> list[tuple[list[Any], bytes]]:
    if not rows:
        payload = encode_json([])
        return [([], payload)]

    parts: list[tuple[list[Any], bytes]] = []
    current: list[Any] = []

    for row in rows:
        candidate = current + [row]
        candidate_bytes = encode_json(candidate)
        if current and len(candidate_bytes) > max_bytes:
            current_bytes = encode_json(current)
            parts.append((current, current_bytes))
            current = [row]
            single_bytes = encode_json(current)
            if len(single_bytes) > max_bytes:
                raise ValueError("Um registro isolado excede o limite máximo de bytes por parte.")
        else:
            current = candidate

    if current:
        parts.append((current, encode_json(current)))
    return parts


def write_part(output: Path, section: str, index: int, payload: bytes, records: int) -> dict[str, Any]:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in section)
    filename = f"{safe}.part-{index:04d}.json"
    (output / filename).write_bytes(payload)
    return {
        "arquivo": filename,
        "bytes": len(payload),
        "sha256": sha256(payload),
        "registros": records,
    }


def main() -> int:
    args = parse_args()
    try:
        if args.max_part_bytes <= 0:
            raise ValueError("--max-part-bytes deve ser maior que zero.")
        if not args.input.is_file():
            raise FileNotFoundError(f"Arquivo de origem não encontrado: {args.input}")
        if not args.release_metadata.is_file():
            raise FileNotFoundError(f"Metadados do Release não encontrados: {args.release_metadata}")

        source_bytes = args.input.read_bytes()
        source = json.loads(source_bytes.decode("utf-8-sig"))
        if not isinstance(source, dict):
            raise ValueError("O JSON mensal deve ter um objeto na raiz.")

        required_arrays = ("dados", "tecnicos", "operacional")
        for name in required_arrays:
            if name not in source or not isinstance(source[name], list):
                raise ValueError(f'O bloco obrigatório "{name}" deve ser uma lista.')

        metadata = json.loads(args.release_metadata.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("Metadados do Release inválidos.")
        if metadata.get("repository") != args.repository:
            raise ValueError("O repositório dos metadados diverge do parâmetro informado.")
        if metadata.get("releaseTag") != args.tag:
            raise ValueError("A tag dos metadados diverge do parâmetro informado.")
        if metadata.get("assetName") != args.asset:
            raise ValueError("O asset dos metadados diverge do parâmetro informado.")

        args.output.mkdir(parents=True, exist_ok=True)
        for old in args.output.glob("*.json"):
            old.unlink()

        sections: dict[str, Any] = {}
        total_bytes = 0
        total_parts = 0

        for section_name, value in source.items():
            descriptors: list[dict[str, Any]] = []
            if isinstance(value, list):
                chunks = split_array(value, args.max_part_bytes)
                offset = 0
                for number, (rows, payload) in enumerate(chunks, start=1):
                    part = write_part(args.output, section_name, number, payload, len(rows))
                    part["inicio"] = offset
                    offset += len(rows)
                    descriptors.append(part)
                    total_bytes += len(payload)
                    total_parts += 1
                sections[section_name] = {
                    "tipo": "array",
                    "registros": len(value),
                    "partes": descriptors,
                }
            else:
                payload = encode_json(value)
                if len(payload) > args.max_part_bytes:
                    raise ValueError(
                        f'A seção de valor "{section_name}" excede o limite de uma parte.'
                    )
                part = write_part(args.output, section_name, 1, payload, 1)
                descriptors.append(part)
                total_bytes += len(payload)
                total_parts += 1
                sections[section_name] = {
                    "tipo": "valor",
                    "registros": 1,
                    "partes": descriptors,
                }

        delivery = {
            "formato": FORMAT,
            "versao": VERSION,
            "competencia": args.competencia,
            "origem": {
                "repositorio": args.repository,
                "tag": args.tag,
                "asset": args.asset,
                "url": args.source_url,
                "apiVersion": metadata.get("apiVersion"),
                "apiReleaseUrl": metadata.get("releaseApiUrl"),
                "apiAssetUrl": metadata.get("assetApiUrl"),
                "assetId": metadata.get("assetId"),
                "assetDigest": metadata.get("assetDigest"),
                "downloadStatusInicial": metadata.get("downloadInitialStatus"),
                "bytes": len(source_bytes),
                "sha256": sha256(source_bytes),
            },
            "secoes": sections,
            "entrega": {
                "totalPartes": total_parts,
                "totalBytes": total_bytes,
                "maxPartBytes": args.max_part_bytes,
            },
        }

        manifest_path = args.output / args.manifest_name
        manifest_path.write_text(
            json.dumps(delivery, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": "ok",
            "manifesto": str(manifest_path),
            "secoes": len(sections),
            "partes": total_parts,
            "bytes": total_bytes,
        }, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
