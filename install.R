#! /usr/local/bin/Rscript
# install R dependencies

# CRAN binaries repo (from image build)
repo <- "https://p3m.dev/cran/__linux__/noble/2025-10-30"

# Guardrail: don’t install into /home in the Docker build context
install_lib <- .libPaths()[1]
if (grepl("^/home", install_lib)) {
  stop(
    "Error: Packages are being installed to /home, which will be removed in the final image. Exiting.",
    call. = FALSE
  )
}

# Main R ecosystem installed via rocker scripts: https://github.com/rocker-org/rocker-versioned2/scripts
# Tidyverse packages are installed via install_tidyverse.sh
# Geospatial packages are installed via install_geospatial.sh

# Extra packages added or ensured to be present

# ------------------------------------------------------------
# 1) Core plumbing + data access + interoperability
# ------------------------------------------------------------
list.of.packages <- c(
  "quarto",
  "reticulate",
  "aws.s3",
  "earthdatalogin",
  "rstac",
  "geonames",
  "isdparser",
  "readHAC",
  "parsedate"
  "tigris",
  "mirai",
  "zarr"
)
install.packages(list.of.packages, repos = repo)

# ------------------------------------------------------------
# 2) Geospatial + mapping + earth/ocean data utilities
# ------------------------------------------------------------
list.of.packages <- c(
  "gdalcubes",
  "rnaturalearth",
  "rnaturalearthdata",
  "PBSmapping",
  "ggspatial",
  "rosm",
  "sfnetworks",
  "marmap",
  "robis",
  "oce",
  "ocedata",
  "plotdap",
  "rerddapXtracto",
  "openair",
  "cmocean"
)
install.packages(list.of.packages, repos = repo)

# ------------------------------------------------------------
# 3) Data wrangling + visualization + reporting
# ------------------------------------------------------------
list.of.packages <- c(
  "reshape2",
  "gridGraphics",
  "matrixStats",
  "plot.matrix",
  "corrplot",
  "cowplot",
  "hexbin",
  "kableExtra",
  "latticeExtra",
  "mapplots",
  "metR",
  "plotly",
  "rasterVis",
  "vioplot"
)
install.packages(list.of.packages, repos = repo)

# ------------------------------------------------------------
# 4) Modeling + time series + statistical tooling
# ------------------------------------------------------------
list.of.packages <- c(
  "caret",
  "biomod2",
  "glmnet",
  "doParallel",
  "earth",
  "fields",
  "dismo",
  "caTools",
  "mda",
  "ape",
  "CircStats",
  "palmerpenguins",
  "forecast",
  "lmtest",
  "tseries",
  "tsibble",
  "urca",
  "akima",
  "smooth",
  "greybox",
  "udunits2"
)
install.packages(list.of.packages, repos = repo)

# TODO: Should they include upgrade=FALSE? eeh: yes to prevent the dependencies from upgrading.
remotes::install_github("hvillalo/echogram", upgrade=FALSE)
remotes::install_github("hvillalo/periods", upgrade=FALSE)
remotes::install_github("hvillalo/satin", upgrade=FALSE)
remotes::install_github("hadley/emo", upgrade=FALSE)
remotes::install_github("JorGarMol/VoCC", upgrade=FALSE)
