"""배포 카탈로그 CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import load_plane_catalog, load_release_manifest, load_service_catalog
from .generator import scaffold_service_assets, sync_generated_files, validate_generated_files


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="OneERP 배포 카탈로그 도구")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="생성 산출물을 갱신한다")
    sub.add_parser("validate", help="생성 산출물 드리프트를 검증한다")
    sub.add_parser("scaffold", help="누락된 Dockerfile/Helm chart를 생성한다")

    args = parser.parse_args()
    root = _root()
    services = load_service_catalog(root)
    planes = load_plane_catalog(root)
    release = load_release_manifest(root)

    if args.command == "sync":
        changed = sync_generated_files(root, services, planes, release)
        for path in changed:
            print(path.relative_to(root))
        return
    if args.command == "validate":
        errors = validate_generated_files(root, services, planes, release)
        if errors:
            for error in errors:
                print(error)
            raise SystemExit(1)
        print("배포 산출물 정합성 통과")
        return
    if args.command == "scaffold":
        changed = scaffold_service_assets(root, services)
        for path in changed:
            print(path.relative_to(root))
        return

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
