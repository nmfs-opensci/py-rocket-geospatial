# py-rocket-geospatial-2

[![Build and Push](https://github.com/nmfs-opensci/py-rocket-geospatial-2/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/nmfs-opensci/py-rocket-geospatial-2/actions/workflows/build-and-push.yml)
[![ghcr.io](https://img.shields.io/badge/ghcr.io-container--images%2Fpy--rocket--geospatial--2-blue?logo=docker)](https://github.com/nmfs-opensci/container-images/pkgs/container/container-images%2Fpy-rocket-geospatial-2)

**Stable Version:** 2025.12.23  
**Dev Version:** 2026.02.08  

```bash
docker pull ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest
docker run -it --rm -p 8888:8888 ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest
```

---

## What is py-rocket-geospatial-2?

**py-rocket-geospatial-2** is a Python–R geospatial Docker image for large-scale earth-science data analysis in JupyterHub environments.

It is designed for users working with large earth-observation datasets, especially cloud-native data, from organizations such as NOAA, NASA, and other public earth-science data providers. The image targets workflows common in cryoscience, oceanography, climate science, and remote sensing. It is optimized for:

- big-data, array-based analysis  
- cloud object storage and distributed computing  
- shared, multi-user JupyterHub deployments  

---

## py-rocket-geospatial-2 combines three ecosystems:

### Python (Pangeo-style big-data stack)
- Based on the Pangeo notebook environment  
- Designed for xarray/Dask-style workflows  
- Extended with additional geospatial and scientific packages  

### R (Rocker-based geospatial environment)
- R installed via Rocker installation scripts  
- RStudio and JupyterLab share the same R environment  
- R runs independently of the conda Python environment  

### Desktop tools for earth science
- Linux desktop via VNC  
- Pre-installed applications commonly used in earth-science workflows: QGIS, Panoply, CoastWatch Utilities  

The image also includes Quarto, TeX Live, MyST, and JupyterBook for scientific publishing.

---

## Runtime overview

- **Python:** 3.11  
  - Conda environment `notebook`, activated on startup  
- **R:** 4.5.x  
  - Shared across RStudio and JupyterLab  

---

## Image structure

- **Base infrastructure** (Jupyter, Dask, Python install, conda setup, R install, and user-experience configuration) lives in  
   [py-rocket-base](https://github.com/nmfs-opensci/py-rocket-base)

- **py-rocket-geospatial-2** adds:
  - Python and R geospatial packages  
  - Desktop applications (QGIS, CoastWatch Utilities, Panoply)  

See the [py-rocket-base documentation](https://nmfs-opensci.github.io/py-rocket-base/) for base image design details.

---

## Reproducibility and validation

This repository automatically maintains pinned and validated package lists:

- `reproducibility/packages-python-pinned.yaml`  
- `reproducibility/packages-r-pinned.R`  
- `reproducibility/build.log`  

Pinned versions are extracted directly from the built image and validated against the requested package lists to support reproducibility and debugging.

---

## Customization and derivative images

### To customize py-rocket-geospatial-2

* edit the Python packages in `conda-env/env-*.yml`
* edit the R packages in `install.R`
* update the QGIS, CoastWatch Utilities, and Panoply installs in `Dockerfile`
* update the systems installs in `apt.txt

If changes affect core platform behavior, please open an issue in  [py-rocket-base](https://github.com/nmfs-opensci/py-rocket-base/issues)

### To create derivative images

1. You can create a derivative image using py-rocket-geospatial-2 as the base. This will add packages to the conda and R environments. For example

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

---

## Provenance

This image was originally maintained under  
https://github.com/nmfs-opensci/container-images

It now lives in its own dedicated repository as part of the NMFS OpenSci container ecosystem.

