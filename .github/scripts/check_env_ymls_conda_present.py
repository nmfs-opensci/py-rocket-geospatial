#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Set, Tuple

def normalize(name: str) -> str:
    return name.strip().lower().replace("_", "-")

def parse_conda_export(path: Path) -> Set[str]:
    """
    Parse conda 'list --export' format:
      name=version=build
    Also tolerates:
      name=version
      name
    Ignores comments and blank lines.
    """
    req: Set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # conda export lines sometimes include channels prefixes; keep it simple:
        # split on '=' and take first token
        name = line.split("=", 1)[0].strip()
        if not name:
            continue
        req.add(normalize(name))
    return req

def docker_conda_list_json(image: str, env: str) -> Dict[str, str]:
    """
    Run `conda list -n <env> --json` inside the container and return {name: version}.
    """
    cmd = ["docker", "run", "--rm", image, "conda", "list", "-n", env, "--json"]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: failed to run conda list inside container.", file=sys.stderr)
        print(e.output, file=sys.stderr)
        raise
    data = json.loads(out)
    installed: Dict[str, str] = {}
    for rec in data:
        n = rec.get("name")
        if not n:
            continue
        installed[normalize(n)] = rec.get("version", "")
    return installed

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="Container image to test")
    ap.add_argument("--env", default="notebook", help="Conda env name (default: notebook)")
    ap.add_argument("--pins", default="packages-python-pinned.yaml",
                    help="Path to conda export pins file (default: packages-python-pinned.yaml)")
    ap.add_argument("--ignore", nargs="*", default=[],
                    help="Optional extra package names to ignore")
    args = ap.parse_args()

    pins_path = Path(args.pins)
    if not pins_path.exists():
        print(f"ERROR: pins file not found: {pins_path}", file=sys.stderr)
        return 2

    required = parse_conda_export(pins_path)
    ignore = {normalize(x) for x in args.ignore}
    required = {p for p in required if p not in ignore}

    installed = docker_conda_list_json(args.image, args.env)

    missing = sorted([p for p in required if p not in installed])

    print(f"Image: {args.image}")
    print(f"Env: {args.env}")
    print(f"Pins file: {pins_path}")
    print(f"Required packages (from pins): {len(required)}")
    print(f"Installed packages (from image): {len(installed)}")
    print()

    if missing:
        print("MISSING packages (present in pins file, absent in image):")
        for m in missing:
            print(f"  - {m}")
        print()
        return 1

    print("OK: all packages in packages-python-pinned.yaml are present in the image.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
