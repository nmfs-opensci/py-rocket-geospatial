# py-rocket-geospatial v2.0

[![Build and Push](https://github.com/nmfs-opensci/py-rocket-geospatial-2/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/nmfs-opensci/py-rocket-geospatial-2/actions/workflows/build-and-push.yml)
[![ghcr.io](https://img.shields.io/badge/ghcr.io-container--images%2Fpy--rocket--geospatial--2-blue?logo=docker)](https://github.com/nmfs-opensci/container-images/pkgs/container/container-images%2Fpy-rocket-geospatial-2)

```bash
docker pull ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest
docker run -it --rm -p 8888:8888 ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest
```

This creates a base Python-R image with geospatial packages for Python and R. The Python environment is the Pangeo notebook environment + extra geospatial libraries (similar to CryoCloud). The R environment is Rocker geospatial plus a few other packages. The image also includes a linux Desktop with QGIS, CoastWatch Utilities, and Panoply.

TeXLive and Quarto are installed along with MyST and JupyterBook.

Python 3.11 is installed with a conda environment called notebook that is activated on opening the container. R 4.5.X is installed and operates separate from the conda notebook environment (conda is not on the PATH when using R). R can be used from RStudio or JupyterLab and the same R environment is used.

## Structure

* The base infrastructure (Jupyter, Dask, Python install, conda env, R install, all the set ups around the user experience) are in [py-rocket-base](https://github.com/nmfs-opensci/py-rocket-base/) which is the base image in the Dockerfile. See the  [py-rocket-base documentation](https://nmfs-opensci.github.io/py-rocket-base/) for information on the base image structure and design.
* py-rocket-geospatial-2 the Python scientific core packages and Python and R geospatial packages. Note the R core scientific packages are in py-rocket-base since rocker_verse is the base R.
* py-rocket-geospatial-2 also installs QGIS, CoastWatch Utilities, and Panoply.

#### Build inputs that determine the image packages
* [Dockerfile](Dockerfile)
* [Python packages (source env files)](conda-env)
* [R packages (source install file)](install.R)
* [system packages](apt.txt)
* [Desktop apps](Desktop)

#### Generated artifacts (reproducibility)
* [Pinned Python packages](reproducibility/packages-python-pinned.yaml) - Auto-generated list of all Python packages with pinned versions
* [Pinned R packages](reproducibility/packages-r-pinned.R) - Auto-generated list of all R packages with pinned versions
* [Build log](reproducibility/build.log) - Validation report


## Customizing py-rocket-geospatial-2

* edit the Python packages here `conda-env/env-*.yml`
* edit the R packages here `install.R`
* update the QGIS, CoastWatch Utilities, and Panoply installs here `Dockerfile`
* update the systems installs here `apt.txt`

If the changes are core functionality, not scientific, put in an [issue in py-rocket-base](https://github.com/nmfs-opensci/py-rocket-base/issues).

### Package Pinning and Validation

The repository automatically maintains pinned package versions with validation:
- `reproducibility/packages-python-pinned.yaml` - Contains Python packages from py-rocket-base environment.yaml and
  conda-env/env-*.yml files with exact versions (not all 900+ conda packages)
  - Packages from py-rocket-base are listed first (including pangeo-notebook and pangeo-dask feedstocks)
  - Packages from conda-env/env-*.yml files are listed second
- `reproducibility/packages-r-pinned.R` - Contains all R packages from the site-library with exact versions
- `reproducibility/build.log` - Validation report showing if all packages from env files and rocker scripts are present

The [Pin Package Versions workflow](.github/workflows/pin-packages.yml):
- Runs automatically after each successful build
- Can be manually triggered from the Actions tab
- Extracts package versions from the published Docker image
- **Extracts py-rocket-base environment.yaml** from /srv/repo in the container image
- **Filters Python packages** to only include those specified in:
  - py-rocket-base environment.yaml (including pangeo-notebook and pangeo-dask feedstock packages)
  - conda-env/env-*.yml files
- **Validates Python packages** that all packages from py-rocket-base and conda-env/env-*.yml files are present in the container
- **Validates R packages** that all packages from install.R, /rocker_scripts/install_geospatial.sh, and /rocker_scripts/install_tidyverse.sh are present in the container
- Creates a PR with:
  - Updated pinned package files
  - reproducibility/build.log with validation results for both Python and R
  - Clear status (✅ SUCCESS or ⚠️ FAILED) in PR description

**On validation success:** All packages are present and pinned.

**On validation failure:** PR includes:
- Filtered list of packages that were successfully installed
- reproducibility/build.log with detailed report of missing packages (both Python and R)
- Action required to investigate and fix installation issues

This provides a complete snapshot of all installed packages for reproducibility and debugging.

## Derivative images

1. You can create a derivative image using py-rocket-geospatial-2 as the base. This will add packages to the conda and R environments.
```
FROM ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:2026.02.08

USER root

COPY . /tmp/
RUN /pyrocket_scripts/install-conda-packages.sh /tmp/your-environment.yml || echo "install-conda-packages.sh failed" || true
RUN /pyrocket_scripts/install-r-packages.sh /tmp/install.R || echo "install-r-package.sh failed" || true
RUN rm -rf /tmp/*

USER ${NB_USER}
WORKDIR ${HOME}
```

2. You can use the https://github.com/nmfs-opensci/py-rocket-geospatial-2/Dockerfile as a template.

3. Making your derivative image build automatically in GitHub from your repo.
   - Copy `.github/actions/build-and-push/action.yml` to the same location in your repo
   - Copy `.github/workflows/build-and-push.yml` into your repo and edit the `image-name`.
   - Set up your repo to allow packages to be published to your location from your repo.

## Provenance

This image used to live at https://github.com/nmfs-opensci/container-images/tree/main/images/py-rocket-geospatial-2 but has now been moved to a dedicated directory. https://github.com/nmfs-opensci/container-images contains other derivative images used in NMFS OpenSci JupyterHubs.
