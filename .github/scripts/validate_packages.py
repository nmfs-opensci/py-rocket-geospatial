#!/usr/bin/env python3
"""
Validate that all Python packages in env-*.yml files are present in packages-python-pinned.yaml.

This script:
1. Parses all env-*.yml files to extract Python package names
2. Parses packages-python-pinned.yaml to get the list of pinned packages
3. Compares the two lists and reports any missing packages
4. Exits with failure if any packages are missing
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Set, Dict, List


def parse_env_files(repo_root: Path) -> Dict[str, Set[str]]:
    """
    Parse all env-*.yml files and extract Python package names.
    
    Returns:
        Dictionary mapping filename to set of package names
    """
    env_files = sorted(repo_root.glob("env-*.yml"))
    packages_by_file = {}
    
    for env_file in env_files:
        with open(env_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                packages = set()
                
                if data and 'dependencies' in data:
                    for dep in data['dependencies']:
                        if isinstance(dep, str):
                            # Extract package name (before version specifiers)
                            # Handle formats like: package, package>=1.0, package~=2.1.1=cpu*
                            pkg_name = re.split(r'[>=<~!]', dep)[0].strip()
                            if pkg_name:
                                packages.add(pkg_name)
                        elif isinstance(dep, dict) and 'pip' in dep:
                            # Handle pip dependencies
                            for pip_dep in dep['pip']:
                                pkg_name = re.split(r'[>=<~!]', pip_dep)[0].strip()
                                if pkg_name:
                                    packages.add(pkg_name)
                
                packages_by_file[env_file.name] = packages
                
            except yaml.YAMLError as e:
                print(f"Error parsing {env_file}: {e}", file=sys.stderr)
                continue
    
    return packages_by_file


def parse_pinned_packages(pinned_file: Path) -> Set[str]:
    """
    Parse packages-python-pinned.yaml to extract package names.
    
    The file format is:
    package_name=version=build_string
    
    Returns:
        Set of package names
    """
    packages = set()
    
    with open(pinned_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Extract package name (before first '=')
            pkg_name = line.split('=')[0].strip()
            if pkg_name:
                packages.add(pkg_name)
    
    return packages


def main():
    """Main function to validate packages."""
    repo_root = Path(__file__).parent.parent.parent
    pinned_file = repo_root / "packages-python-pinned.yaml"
    
    # Check if pinned file exists
    if not pinned_file.exists():
        print(f"Error: {pinned_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse files
    print("Parsing env-*.yml files...")
    packages_by_file = parse_env_files(repo_root)
    
    if not packages_by_file:
        print("Warning: No env-*.yml files found", file=sys.stderr)
        sys.exit(0)
    
    print(f"Found {len(packages_by_file)} env files")
    
    print(f"\nParsing {pinned_file.name}...")
    pinned_packages = parse_pinned_packages(pinned_file)
    print(f"Found {len(pinned_packages)} pinned packages")
    
    # Collect all packages from env files
    all_env_packages = set()
    for packages in packages_by_file.values():
        all_env_packages.update(packages)
    
    print(f"\nTotal unique packages in env files: {len(all_env_packages)}")
    
    # Find missing packages
    missing_packages = all_env_packages - pinned_packages
    
    if missing_packages:
        print("\n" + "=" * 70)
        print("VALIDATION FAILED: Missing packages in packages-python-pinned.yaml")
        print("=" * 70)
        print("\nThe following packages are in env-*.yml files but not in packages-python-pinned.yaml:\n")
        
        for pkg in sorted(missing_packages):
            # Find which env files contain this package
            sources = [fname for fname, pkgs in packages_by_file.items() if pkg in pkgs]
            print(f"  - {pkg}")
            print(f"    Found in: {', '.join(sources)}")
        
        print(f"\nTotal missing packages: {len(missing_packages)}")
        print("\nPlease ensure these packages are installed in the container image")
        print("or remove them from the env files if they're not needed.")
        print("=" * 70)
        sys.exit(1)
    else:
        print("\n" + "=" * 70)
        print("VALIDATION PASSED: All packages are present!")
        print("=" * 70)
        print("\nAll packages from env-*.yml files are present in packages-python-pinned.yaml")
        sys.exit(0)


if __name__ == "__main__":
    main()
