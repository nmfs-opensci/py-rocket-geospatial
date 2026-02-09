#!/usr/bin/env python3
"""
Filter packages-python-pinned.yaml to only include packages from env-*.yml files,
then validate that all packages in env files are present.

This script:
1. Parses all env-*.yml files to extract Python package names
2. Reads the full packages-python-pinned.yaml (all conda packages)
3. Filters to only include packages that are in env files
4. Writes the filtered list back to packages-python-pinned.yaml
5. Validates that all env packages are present in the filtered list
6. Writes results to build.log
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple


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


def read_pinned_packages(pinned_file: Path) -> Tuple[Dict[str, str], List[str]]:
    """
    Parse packages-python-pinned.yaml to extract package names and full lines.
    
    Returns:
        Tuple of (dictionary mapping package name to full line, list of header lines)
    """
    packages = {}
    header_lines = []
    in_header = True
    
    with open(pinned_file, 'r') as f:
        for line in f:
            stripped = line.strip()
            # Keep header comments
            if stripped.startswith('#') or not stripped:
                if in_header:
                    header_lines.append(line)
                continue
            
            in_header = False
            # Extract package name (before first '=')
            pkg_name = stripped.split('=')[0].strip()
            if pkg_name:
                packages[pkg_name] = line.rstrip('\n')
    
    return packages, header_lines


def write_filtered_packages(pinned_file: Path, header_lines: List[str], 
                            filtered_packages: Dict[str, str]):
    """
    Write filtered packages back to packages-python-pinned.yaml.
    """
    with open(pinned_file, 'w') as f:
        # Write header
        for line in header_lines:
            f.write(line)
        
        # Write filtered packages in alphabetical order
        for pkg_name in sorted(filtered_packages.keys()):
            f.write(filtered_packages[pkg_name] + '\n')


def write_build_log(log_file: Path, success: bool, missing_packages: Set[str],
                   packages_by_file: Dict[str, Set[str]], 
                   total_env_packages: int, total_pinned: int):
    """
    Write build.log with validation results.
    """
    with open(log_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Python Package Validation Report\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Total unique packages in env-*.yml files: {total_env_packages}\n")
        f.write(f"Total packages in filtered packages-python-pinned.yaml: {total_pinned}\n\n")
        
        if success:
            f.write("STATUS: SUCCESS\n")
            f.write("=" * 70 + "\n\n")
            f.write("All Python packages from env-*.yml files are present in the\n")
            f.write("container image and have been pinned in packages-python-pinned.yaml.\n\n")
            f.write("The pinned file now contains only the packages specified in env files,\n")
            f.write("not all 900+ packages from the conda environment.\n")
        else:
            f.write("STATUS: FAILED\n")
            f.write("=" * 70 + "\n\n")
            f.write("The following packages are in env-*.yml files but were NOT found\n")
            f.write("in the container image:\n\n")
            
            for pkg in sorted(missing_packages):
                sources = [fname for fname, pkgs in packages_by_file.items() if pkg in pkgs]
                f.write(f"  - {pkg}\n")
                f.write(f"    Found in: {', '.join(sources)}\n")
            
            f.write(f"\nTotal missing packages: {len(missing_packages)}\n\n")
            f.write("To resolve this issue:\n")
            f.write("  1. Check if these packages failed to install in the container\n")
            f.write("  2. Review the container build logs for errors\n")
            f.write("  3. Fix any installation issues and rebuild the container\n")
            f.write("  4. If packages are not needed, remove them from env-*.yml files\n")
        
        f.write("\n" + "=" * 70 + "\n")


def main():
    """Main function to filter and validate packages."""
    repo_root = Path(__file__).parent.parent.parent
    pinned_file = repo_root / "packages-python-pinned.yaml"
    log_file = repo_root / "build.log"
    
    # Check if pinned file exists
    if not pinned_file.exists():
        print(f"Error: {pinned_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse env files
    print("Parsing env-*.yml files...")
    packages_by_file = parse_env_files(repo_root)
    
    if not packages_by_file:
        print("Warning: No env-*.yml files found", file=sys.stderr)
        sys.exit(0)
    
    print(f"Found {len(packages_by_file)} env files")
    
    # Collect all packages from env files
    all_env_packages = set()
    for packages in packages_by_file.values():
        all_env_packages.update(packages)
    
    print(f"Total unique packages in env files: {len(all_env_packages)}")
    
    # Read all pinned packages
    print(f"\nReading {pinned_file.name}...")
    all_pinned_packages, header_lines = read_pinned_packages(pinned_file)
    print(f"Found {len(all_pinned_packages)} total pinned packages")
    
    # Filter to only packages in env files
    filtered_packages = {}
    for pkg_name in all_env_packages:
        if pkg_name in all_pinned_packages:
            filtered_packages[pkg_name] = all_pinned_packages[pkg_name]
    
    print(f"Filtered to {len(filtered_packages)} packages from env files")
    
    # Find missing packages
    missing_packages = all_env_packages - set(filtered_packages.keys())
    
    # Write filtered packages back
    print(f"\nWriting filtered packages to {pinned_file.name}...")
    write_filtered_packages(pinned_file, header_lines, filtered_packages)
    
    # Determine success
    success = len(missing_packages) == 0
    
    # Write build log
    print(f"Writing validation results to {log_file.name}...")
    write_build_log(log_file, success, missing_packages, packages_by_file,
                   len(all_env_packages), len(filtered_packages))
    
    # Print results
    print("\n" + "=" * 70)
    if success:
        print("SUCCESS: All packages validated and pinned")
        print("=" * 70)
        print(f"\npackages-python-pinned.yaml now contains {len(filtered_packages)} packages")
        print("(only those specified in env-*.yml files)")
        print(f"\nSee {log_file.name} for full report")
        sys.exit(0)
    else:
        print("FAILED: Some packages are missing")
        print("=" * 70)
        print(f"\n{len(missing_packages)} packages from env files not found in container")
        print(f"\nSee {log_file.name} for details")
        sys.exit(0)  # Exit 0 so workflow continues to create PR


if __name__ == "__main__":
    main()
