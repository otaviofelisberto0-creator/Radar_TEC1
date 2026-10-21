#!/usr/bin/env python3
"""Valida hashes, contagens e equivalência da entrega fracionada TEC1."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_FORMAT = "tec1-json-shards-v1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--site", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    site = args.site.resolve()
    manifest_path = site / args.manifest
    source_path = args.source.resolve()
    try:
        delivery = json.loads(manifest_path.read_text("utf-8"))
        source_bytes = source_path.read_bytes()
        if delivery.get("formato") != EXPECTED_FORMAT:
            raise ValueError("Formato de entrega incorreto.")
        if delivery["origem"]["bytes"] != len(source_bytes):
            raise ValueError("Tamanho da origem divergente.")
        if delivery["origem"]["sha256"] != sha256(source_bytes):
            raise ValueError("SHA-256 da origem divergente.")
        if delivery.get("versao") != 2:
            raise ValueError("Versão do manifesto de entrega incorreta.")
        origin = delivery["origem"]
        if origin.get("downloadStatusInicial") not in (200, 302):
            raise ValueError("Status inicial do download oficial deve ser 200 ou 302.")
        if not str(origin.get("apiReleaseUrl") or "").startswith("https://api.github.com/repos/"):
            raise ValueError("URL oficial da API da Release ausente ou inválida.")
        if not str(origin.get("apiAssetUrl") or "").startswith("https://api.github.com/repos/"):
            raise ValueError("URL oficial da API do asset ausente ou inválida.")
        asset_digest = str(origin.get("assetDigest") or "")
        if asset_digest.startswith("sha256:") and asset_digest.split(":", 1)[1].lower() != origin["sha256"]:
            raise ValueError("Digest oficial do asset diverge do SHA-256 da origem.")
        source = json.loads(source_bytes.decode("utf-8-sig"))
        del source_bytes

        base = manifest_path.parent
        seen: set[str] = set()
        total_bytes = 0
        total_parts = 0
        for section_name, descriptor in delivery["secoes"].items():
            if section_name not in source:
                raise ValueError(f"Seção inesperada: {section_name}")
            expected: Any = source[section_name]
            parts = descriptor.get("partes") or []
            if not parts:
                raise ValueError(f"Seção sem partes: {section_name}")
            if descriptor["tipo"] == "array":
                if not isinstance(expected, list):
                    raise ValueError(f"Tipo divergente na seção {section_name}")
                offset = 0
                for part in parts:
                    rel = part["arquivo"]
                    if rel in seen:
                        raise ValueError(f"Parte duplicada: {rel}")
                    seen.add(rel)
                    payload = (base / rel).read_bytes()
                    if len(payload) != part["bytes"] or sha256(payload) != part["sha256"]:
                        raise ValueError(f"Integridade inválida: {rel}")
                    rows = json.loads(payload.decode("utf-8"))
                    if not isinstance(rows, list) or len(rows) != part["registros"]:
                        raise ValueError(f"Contagem inválida: {rel}")
                    if rows != expected[offset:offset + len(rows)]:
                        raise ValueError(f"Conteúdo divergente: {rel}")
                    offset += len(rows)
                    total_bytes += len(payload)
                    total_parts += 1
                if offset != len(expected) or descriptor["registros"] != len(expected):
                    raise ValueError(f"Total divergente: {section_name}")
            elif descriptor["tipo"] == "valor":
                if len(parts) != 1:
                    raise ValueError(f"Valor com múltiplas partes: {section_name}")
                part = parts[0]
                rel = part["arquivo"]
                payload = (base / rel).read_bytes()
                if len(payload) != part["bytes"] or sha256(payload) != part["sha256"]:
                    raise ValueError(f"Integridade inválida: {rel}")
                if json.loads(payload.decode("utf-8")) != expected:
                    raise ValueError(f"Conteúdo divergente: {rel}")
                seen.add(rel)
                total_bytes += len(payload)
                total_parts += 1
            else:
                raise ValueError(f"Tipo de seção inválido: {section_name}")

        if set(source) != set(delivery["secoes"]):
            raise ValueError("Nem todas as seções da origem foram publicadas.")
        if total_bytes != delivery["entrega"]["totalBytes"]:
            raise ValueError("Total de bytes da entrega divergente.")
        if total_parts != delivery["entrega"]["totalPartes"]:
            raise ValueError("Total de partes divergente.")
        print(json.dumps({
            "status": "ok",
            "secoes": len(delivery["secoes"]),
            "partes": total_parts,
            "bytes": total_bytes,
            "sha256Origem": delivery["origem"]["sha256"],
        }, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
