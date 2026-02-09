#!/usr/bin/env python3
"""
Filter packages-python-pinned.yaml to only include packages from env-*.yml files
and py-rocket-base environment.yaml, then validate that all packages are present.

This script:
1. Parses py-rocket-base environment.yaml to extract Python package names (including pangeo-notebook and pangeo-dask feedstocks)
2. Parses all env-*.yml files to extract Python package names
3. Reads the full packages-python-pinned.yaml (all conda packages)
4. Filters to only include packages that are in env files or py-rocket-base
5. Writes the filtered list back to packages-python-pinned.yaml with proper organization
6. Validates that all packages are present in the filtered list
7. Writes results to build.log
"""

import sys
import yaml
import re
from pathlib import Path
from typing import Set, Dict, List, Tuple


def parse_base_environment(base_env_file: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    Parse py-rocket-base environment.yaml and extract Python package names.
    This includes packages from pangeo-notebook and pangeo-dask feedstocks,
    and all other packages listed in the file.
    
    Returns:
        Tuple of (pangeo_notebook_packages, pangeo_dask_packages, other_base_packages)
    """
    # Known packages from pangeo-notebook feedstock (from meta.yaml)
    pangeo_notebook_packages = {
        'pangeo-dask',
        'dask-labextension',
        'ipywidgets',
        'jupyter-server-proxy',
        'jupyterhub-singleuser',
        'jupyterlab',
        'nbgitpuller'
    }
    
    # Known packages from pangeo-dask feedstock (from meta.yaml)
    pangeo_dask_packages = {
        'dask',
        'distributed',
        'dask-gateway'
    }
    
    # All packages from the environment.yml
    all_base_packages = set()
    
    if base_env_file.exists():
        with open(base_env_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                
                if data and 'dependencies' in data:
                    for dep in data['dependencies']:
                        if isinstance(dep, str):
                            # Extract package name (before version specifiers)
                            pkg_name = re.split(r'[>=<~!]', dep)[0].strip()
                            # Exclude python itself and pip (not conda packages in the traditional sense)
                            if pkg_name and pkg_name not in ['python', 'pip']:
                                all_base_packages.add(pkg_name)
                        elif isinstance(dep, dict) and 'pip' in dep:
                            # Handle pip dependencies
                            for pip_dep in dep['pip']:
                                pkg_name = re.split(r'[>=<~!]', pip_dep)[0].strip()
                                if pkg_name:
                                    all_base_packages.add(pkg_name)
                
            except yaml.YAMLError as e:
                print(f"Error parsing {base_env_file}: {e}", file=sys.stderr)
    
    # Separate other packages (not in pangeo feedstocks)
    other_base_packages = all_base_packages - pangeo_notebook_packages - pangeo_dask_packages
    
    return pangeo_notebook_packages, pangeo_dask_packages, other_base_packages


def parse_env_files(repo_root: Path) -> Dict[str, Set[str]]:
    """
    Parse all env-*.yml files and extract Python package names.
    
    Returns:
        Dictionary mapping filename to set of package names
    """
    env_dir = repo_root / "environment"
    env_files = sorted(env_dir.glob("env-*.yml"))
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
                            pangeo_notebook_packages: Dict[str, str],
                            pangeo_dask_packages: Dict[str, str],
                            other_base_packages: Dict[str, str],
                            env_packages: Dict[str, str]):
    """
    Write filtered packages back to packages-python-pinned.yaml.
    Organizes output with separate sections for pangeo feedstocks and other base packages.
    """
    with open(pinned_file, 'w') as f:
        # Write header
        for line in header_lines:
            f.write(line)
        
        # Write pangeo-notebook feedstock packages
        if pangeo_notebook_packages:
            f.write('\n# Packages from pangeo-notebook feedstock\n')
            for pkg_name in sorted(pangeo_notebook_packages.keys()):
                f.write(pangeo_notebook_packages[pkg_name] + '\n')
        
        # Write pangeo-dask feedstock packages
        if pangeo_dask_packages:
            f.write('\n# Packages from pangeo-dask feedstock\n')
            for pkg_name in sorted(pangeo_dask_packages.keys()):
                f.write(pangeo_dask_packages[pkg_name] + '\n')
        
        # Write other py-rocket-base packages
        if other_base_packages:
            f.write('\n# Other packages from py-rocket-base environment.yaml\n')
            for pkg_name in sorted(other_base_packages.keys()):
                f.write(other_base_packages[pkg_name] + '\n')
        
        # Write env-*.yml packages
        if env_packages:
            f.write('\n# Packages from environment/env-*.yml files\n')
            for pkg_name in sorted(env_packages.keys()):
                f.write(env_packages[pkg_name] + '\n')


def write_build_log(log_file: Path, success: bool, missing_packages: Set[str],
                   packages_by_file: Dict[str, Set[str]], 
                   total_pangeo_notebook: int,
                   total_pangeo_dask: int,
                   total_other_base: int,
                   total_env_packages: int, total_pinned: int):
    """
    Write build.log with validation results.
    """
    with open(log_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Python Package Validation Report\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Packages from pangeo-notebook feedstock: {total_pangeo_notebook}\n")
        f.write(f"Packages from pangeo-dask feedstock: {total_pangeo_dask}\n")
        f.write(f"Other packages from py-rocket-base: {total_other_base}\n")
        f.write(f"Total packages from py-rocket-base: {total_pangeo_notebook + total_pangeo_dask + total_other_base}\n")
        f.write(f"Total unique packages in env-*.yml files: {total_env_packages}\n")
        f.write(f"Total packages in filtered packages-python-pinned.yaml: {total_pinned}\n\n")
        
        if success:
            f.write("STATUS: SUCCESS\n")
            f.write("=" * 70 + "\n\n")
            f.write("All Python packages from py-rocket-base environment.yaml and\n")
            f.write("env-*.yml files are present in the container image and have been\n")
            f.write("pinned in packages-python-pinned.yaml.\n\n")
            f.write("The pinned file includes:\n")
            f.write("  - Packages from pangeo-notebook feedstock\n")
            f.write("  - Packages from pangeo-dask feedstock\n")
            f.write("  - Other packages from py-rocket-base\n")
            f.write("  - Packages from environment/env-*.yml files\n")
            f.write("\nNot all 900+ packages from the conda environment are included.\n")
        else:
            f.write("STATUS: FAILED\n")
            f.write("=" * 70 + "\n\n")
            f.write("The following packages are in env-*.yml or py-rocket-base files\n")
            f.write("but were NOT found in the container image:\n\n")
            
            for pkg in sorted(missing_packages):
                sources = [fname for fname, pkgs in packages_by_file.items() if pkg in pkgs]
                f.write(f"  - {pkg}\n")
                if sources:
                    f.write(f"    Found in: {', '.join(sources)}\n")
                else:
                    f.write(f"    Found in: py-rocket-base environment.yaml\n")
            
            f.write(f"\nTotal missing packages: {len(missing_packages)}\n\n")
            f.write("To resolve this issue:\n")
            f.write("  1. Check if these packages failed to install in the container\n")
            f.write("  2. Review the container build logs for errors\n")
            f.write("  3. Fix any installation issues and rebuild the container\n")
            f.write("  4. If packages are not needed, remove them from the respective files\n")
        
        f.write("\n" + "=" * 70 + "\n")


def main():
    """Main function to filter and validate packages."""
    repo_root = Path(__file__).parent.parent.parent
    pinned_file = repo_root / "packages-python-pinned.yaml"
    log_file = repo_root / "build.log"
    base_env_file = repo_root / "base-environment.yaml"
    
    # Check if pinned file exists
    if not pinned_file.exists():
        print(f"Error: {pinned_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse py-rocket-base environment.yaml
    print("Parsing py-rocket-base environment.yaml...")
    pangeo_notebook_set, pangeo_dask_set, other_base_set = parse_base_environment(base_env_file)
    all_base_packages = pangeo_notebook_set | pangeo_dask_set | other_base_set
    print(f"Found {len(pangeo_notebook_set)} packages from pangeo-notebook feedstock")
    print(f"Found {len(pangeo_dask_set)} packages from pangeo-dask feedstock")
    print(f"Found {len(other_base_set)} other packages from py-rocket-base")
    print(f"Total packages from py-rocket-base: {len(all_base_packages)}")
    
    # Parse env files
    print("\nParsing env-*.yml files...")
    packages_by_file = parse_env_files(repo_root)
    
    if not packages_by_file:
        print("Warning: No env-*.yml files found. Processing will continue with base packages only.", file=sys.stderr)
    
    print(f"Found {len(packages_by_file)} env files")
    
    # Collect all packages from env files
    all_env_packages = set()
    for packages in packages_by_file.values():
        all_env_packages.update(packages)
    
    print(f"Total unique packages in env files: {len(all_env_packages)}")
    
    # Combine all packages we want to include
    all_target_packages = all_base_packages | all_env_packages
    print(f"\nTotal packages to include: {len(all_target_packages)}")
    
    # Read all pinned packages
    print(f"\nReading {pinned_file.name}...")
    all_pinned_packages, header_lines = read_pinned_packages(pinned_file)
    print(f"Found {len(all_pinned_packages)} total pinned packages")
    
    # Filter to packages from pangeo-notebook feedstock
    pangeo_notebook_filtered = {}
    for pkg_name in pangeo_notebook_set:
        if pkg_name in all_pinned_packages:
            pangeo_notebook_filtered[pkg_name] = all_pinned_packages[pkg_name]
    
    print(f"Filtered to {len(pangeo_notebook_filtered)} packages from pangeo-notebook feedstock")
    
    # Filter to packages from pangeo-dask feedstock
    pangeo_dask_filtered = {}
    for pkg_name in pangeo_dask_set:
        if pkg_name in all_pinned_packages:
            pangeo_dask_filtered[pkg_name] = all_pinned_packages[pkg_name]
    
    print(f"Filtered to {len(pangeo_dask_filtered)} packages from pangeo-dask feedstock")
    
    # Filter to other packages from py-rocket-base
    other_base_filtered = {}
    for pkg_name in other_base_set:
        if pkg_name in all_pinned_packages:
            other_base_filtered[pkg_name] = all_pinned_packages[pkg_name]
    
    print(f"Filtered to {len(other_base_filtered)} other packages from py-rocket-base")
    
    # Filter to packages from env files
    env_filtered = {}
    for pkg_name in all_env_packages:
        if pkg_name in all_pinned_packages:
            env_filtered[pkg_name] = all_pinned_packages[pkg_name]
    
    print(f"Filtered to {len(env_filtered)} packages from env files")
    
    # Find missing packages
    all_filtered = set(pangeo_notebook_filtered.keys()) | set(pangeo_dask_filtered.keys()) | set(other_base_filtered.keys()) | set(env_filtered.keys())
    missing_packages = all_target_packages - all_filtered
    
    # Write filtered packages back
    print(f"\nWriting filtered packages to {pinned_file.name}...")
    write_filtered_packages(pinned_file, header_lines, pangeo_notebook_filtered, 
                           pangeo_dask_filtered, other_base_filtered, env_filtered)
    
    # Determine success
    success = len(missing_packages) == 0
    
    # Write build log
    print(f"Writing validation results to {log_file.name}...")
    write_build_log(log_file, success, missing_packages, packages_by_file,
                   len(pangeo_notebook_set), len(pangeo_dask_set), len(other_base_set),
                   len(all_env_packages), len(all_filtered))
    
    # Print results
    print("\n" + "=" * 70)
    if success:
        print("SUCCESS: All packages validated and pinned")
        print("=" * 70)
        print(f"\npackages-python-pinned.yaml now contains {len(all_filtered)} packages:")
        print(f"  - {len(pangeo_notebook_filtered)} from pangeo-notebook feedstock")
        print(f"  - {len(pangeo_dask_filtered)} from pangeo-dask feedstock")
        print(f"  - {len(other_base_filtered)} other from py-rocket-base")
        print(f"  - {len(env_filtered)} from env-*.yml files")
        print(f"\nSee {log_file.name} for full report")
        sys.exit(0)
    else:
        print("FAILED: Some packages are missing")
        print("=" * 70)
        print(f"\n{len(missing_packages)} packages not found in container")
        print(f"\nSee {log_file.name} for details")
        sys.exit(0)  # Exit 0 so workflow continues to create PR


if __name__ == "__main__":
    main()
