#!/usr/bin/env python3
"""
Validate R packages from install.R and rocker scripts against packages-r-pinned.R.

This script:
1. Extracts package names from install.R
2. Extracts package names from /rocker_scripts/install_geospatial.sh (from container)
3. Extracts package names from /rocker_scripts/install_tidyverse.sh (from container)
4. Reads packages from packages-r-pinned.R
5. Validates that all packages are present in the pinned file
6. Appends results to build.log
"""

import sys
import re
from pathlib import Path
from typing import Set, Dict, List


def parse_install_r(install_r_path: Path) -> Set[str]:
    """
    Parse install.R and extract R package names.
    
    Returns:
        Set of package names
    """
    packages = set()
    
    with open(install_r_path, 'r') as f:
        content = f.read()
        
        # Find install.packages() calls with vectors
        # e.g., list.of.packages <- c("quarto", "reticulate", ...)
        vector_pattern = r'c\s*\(\s*([^)]+)\s*\)'
        for match in re.finditer(vector_pattern, content):
            vector_content = match.group(1)
            # Extract quoted package names
            pkg_names = re.findall(r'["\']([^"\']+)["\']', vector_content)
            packages.update(pkg_names)
        
        # Find remotes::install_github() calls
        # e.g., remotes::install_github("hvillalo/echogram", ...)
        github_pattern = r'remotes::install_github\s*\(\s*["\']([^/]+)/([^"\'@]+)'
        for match in re.finditer(github_pattern, content):
            repo_name = match.group(2)
            packages.add(repo_name)
    
    return packages


def parse_install_geospatial_content(script_content: str) -> Set[str]:
    """
    Parse install_geospatial.sh content and extract R package names.
    
    Returns:
        Set of package names
    """
    packages = set()
    
    # Find install2.r commands
    # The install2.r command spans multiple lines with backslash continuation
    lines = script_content.split('\n')
    in_install2r = False
    
    for line in lines:
        # Check if this line starts install2.r command
        if 'install2.r' in line and not line.strip().startswith('#'):
            in_install2r = True
            continue
        
        # If we're in an install2.r block
        if in_install2r:
            stripped = line.strip()
            # Empty line ends the block
            if not stripped or stripped.startswith('#'):
                in_install2r = False
                continue
            
            # Extract package name (remove backslash if present)
            pkg_name = stripped.rstrip('\\').strip()
            
            # Skip if it looks like a flag or empty or variable
            if pkg_name and not pkg_name.startswith('-') and not pkg_name.startswith('$'):
                # Stop if we hit something that looks like a new command
                if any(cmd in pkg_name for cmd in ['R ', 'R\t', 'apt', 'set ', 'export', 'echo']):
                    in_install2r = False
                    continue
                packages.add(pkg_name)
            
            # Check if line does NOT end with backslash (end of continuation)
            if not stripped.endswith('\\'):
                in_install2r = False
    
    # Find BiocManager::install() calls
    # e.g., R -e "BiocManager::install('rhdf5')"
    bioc_pattern = r'BiocManager::install\s*\(\s*["\']([^"\']+)["\']'
    for match in re.finditer(bioc_pattern, script_content):
        packages.add(match.group(1))
    
    return packages


def read_pinned_packages(pinned_file: Path) -> Set[str]:
    """
    Parse packages-r-pinned.R to extract package names.
    
    Returns:
        Set of package names
    """
    packages = set()
    
    with open(pinned_file, 'r') as f:
        for line in f:
            stripped = line.strip()
            
            # Skip comments and empty lines
            if stripped.startswith('#') or not stripped:
                continue
            
            # Match remotes::install_version("package", ...)
            version_match = re.match(
                r'remotes::install_version\s*\(\s*["\']([^"\']+)["\']',
                stripped
            )
            if version_match:
                packages.add(version_match.group(1))
                continue
            
            # Match remotes::install_github("user/repo", ...)
            github_match = re.match(
                r'remotes::install_github\s*\(\s*["\']([^/]+)/([^"\'@]+)',
                stripped
            )
            if github_match:
                packages.add(github_match.group(2))
                continue
    
    return packages


def append_to_build_log(log_file: Path, success: bool, missing_packages: Set[str],
                       install_r_packages: Set[str], geospatial_packages: Set[str],
                       tidyverse_packages: Set[str], total_expected: int, total_pinned: int):
    """
    Append R package validation results to build.log.
    """
    with open(log_file, 'a') as f:
        f.write("\n\n")
        f.write("=" * 70 + "\n")
        f.write("R Package Validation Report\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Packages in install.R: {len(install_r_packages)}\n")
        f.write(f"Packages in /rocker_scripts/install_geospatial.sh: {len(geospatial_packages)}\n")
        f.write(f"Packages in /rocker_scripts/install_tidyverse.sh: {len(tidyverse_packages)}\n")
        f.write(f"Total unique R packages expected: {total_expected}\n")
        f.write(f"Total packages in packages-r-pinned.R: {total_pinned}\n\n")
        
        if success:
            f.write("STATUS: SUCCESS\n")
            f.write("=" * 70 + "\n\n")
            f.write("All R packages from install.R, install_geospatial.sh, and\n")
            f.write("install_tidyverse.sh are present in packages-r-pinned.R.\n\n")
            f.write("The packages-r-pinned.R file contains all required packages\n")
            f.write("from the custom install.R and the rocker scripts.\n")
        else:
            f.write("STATUS: FAILED\n")
            f.write("=" * 70 + "\n\n")
            f.write("The following R packages are specified in install.R,\n")
            f.write("install_geospatial.sh, or install_tidyverse.sh but were NOT\n")
            f.write("found in packages-r-pinned.R:\n\n")
            
            for pkg in sorted(missing_packages):
                sources = []
                if pkg in install_r_packages:
                    sources.append("install.R")
                if pkg in geospatial_packages:
                    sources.append("install_geospatial.sh")
                if pkg in tidyverse_packages:
                    sources.append("install_tidyverse.sh")
                f.write(f"  - {pkg}\n")
                f.write(f"    Found in: {', '.join(sources)}\n")
            
            f.write(f"\nTotal missing packages: {len(missing_packages)}\n\n")
            f.write("To resolve this issue:\n")
            f.write("  1. Check if these packages failed to install in the container\n")
            f.write("  2. Review the container build logs for errors\n")
            f.write("  3. Fix any installation issues and rebuild the container\n")
            f.write("  4. Re-run the pin-packages workflow to update packages-r-pinned.R\n")
        
        f.write("\n" + "=" * 70 + "\n")


def main():
    """Main function to validate R packages."""
    repo_root = Path(__file__).parent.parent.parent
    install_r_path = repo_root / "install.R"
    pinned_file = repo_root / "packages-r-pinned.R"
    log_file = repo_root / "build.log"
    
    # Temporary files created by workflow with rocker script content
    geospatial_file = Path("/tmp/install_geospatial.sh")
    tidyverse_file = Path("/tmp/install_tidyverse.sh")
    
    # Check if required files exist
    if not install_r_path.exists():
        print(f"Error: {install_r_path} not found", file=sys.stderr)
        sys.exit(1)
    
    if not pinned_file.exists():
        print(f"Error: {pinned_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse install.R
    print("Parsing install.R...")
    install_r_packages = parse_install_r(install_r_path)
    print(f"Found {len(install_r_packages)} packages in install.R")
    
    # Read install_geospatial.sh content
    print("\nReading install_geospatial.sh content...")
    if geospatial_file.exists():
        with open(geospatial_file, 'r') as f:
            geospatial_content = f.read()
        geospatial_packages = parse_install_geospatial_content(geospatial_content)
        print(f"Found {len(geospatial_packages)} packages in install_geospatial.sh")
    else:
        print("Warning: install_geospatial.sh file not found", file=sys.stderr)
        geospatial_packages = set()
    
    # Read install_tidyverse.sh content
    print("\nReading install_tidyverse.sh content...")
    if tidyverse_file.exists():
        with open(tidyverse_file, 'r') as f:
            tidyverse_content = f.read()
        tidyverse_packages = parse_install_geospatial_content(tidyverse_content)  # Same parser works for both
        print(f"Found {len(tidyverse_packages)} packages in install_tidyverse.sh")
    else:
        print("Warning: install_tidyverse.sh file not found", file=sys.stderr)
        tidyverse_packages = set()
    
    # Combine all expected packages
    all_expected_packages = install_r_packages | geospatial_packages | tidyverse_packages
    print(f"\nTotal unique R packages expected: {len(all_expected_packages)}")
    
    # Read pinned packages
    print(f"\nReading {pinned_file.name}...")
    pinned_packages = read_pinned_packages(pinned_file)
    print(f"Found {len(pinned_packages)} packages in {pinned_file.name}")
    
    # Find missing packages
    missing_packages = all_expected_packages - pinned_packages
    
    # Determine success
    success = len(missing_packages) == 0
    
    # Append to build log
    print(f"\nAppending R validation results to {log_file.name}...")
    append_to_build_log(log_file, success, missing_packages,
                       install_r_packages, geospatial_packages, tidyverse_packages,
                       len(all_expected_packages), len(pinned_packages))
    
    # Print results
    print("\n" + "=" * 70)
    if success:
        print("SUCCESS: All R packages validated")
        print("=" * 70)
        print(f"\nAll {len(all_expected_packages)} expected R packages are present")
        print(f"in {pinned_file.name}")
        print(f"\nSee {log_file.name} for full report")
        sys.exit(0)
    else:
        print("FAILED: Some R packages are missing")
        print("=" * 70)
        print(f"\n{len(missing_packages)} R packages not found in {pinned_file.name}")
        print(f"\nSee {log_file.name} for details")
        sys.exit(0)  # Exit 0 so workflow continues to create PR


if __name__ == "__main__":
    main()
