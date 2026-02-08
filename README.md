# py-rocket-geospatial v2.0

This creates a base Python-R image with geospatial packages for Python and R. The Python environment is the Pangeo notebook environment + extra geospatial libraries (similar to CryoCloud). The R environment is Rocker geospatial plus a few other packages. The image also includes a linux Desktop with QGIS, CoastWatch Utilities, and Panoply.

TeXLive and Quarto are installed along with MyST and JupyterBook.

Python 3.11 is installed with a conda environment called notebook that is activated on opening the container. R 4.5.X is installed and operates separate from the conda notebook environment (conda is not on the PATH when using R). R can be used from RStudio or JupyterLab and the same R environment is used.

See the documentation on [py-rocket-base](https://nmfs-opensci.github.io/py-rocket-base/) for information on the image structure and design.

## Provenance

This image used to live at https://github.com/nmfs-opensci/container-images/tree/main/images/py-rocket-geospatial-2 but has now been moved to a dedicated directory. https://github.com/nmfs-opensci/container-images contains other derivative images used in NMFS OpenSci JupyterHubs.
