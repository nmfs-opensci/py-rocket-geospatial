# Changes

## 2026-02-08

* In January 2026, the solver stopped solving. It was also getting long, over an hour. I broke the main environment file into 5 smaller files (conda-env/env-*.yml) and add these sequentially to the conda notebook env. This seemed to fix the impossible to solve environment.
* Removed some unneeded packages
* The R package installs were messed up. First install_geospatial.sh needs to be run first. Then other packages.
    - When I fixed the problem of installs going to /home (and then getting wiped out), I caused installs via install-r-packages.sh to go to source rather than binary.
    - There were a bunch of OHW R packages that I needed to add.
 
## 2026-02-07

Moved py-rocket-geospatial-2 to its own dedicated directory here.
