# Changes

## 2026-02-07

* In January, the solver stopped solving. It was also getting long, over an hour. I broke the environment.yml into 5 smaller files and add these sequentially to the conda notebook env. This seemed to solve the impossible to solve environment.
* Removed some unneeded packages
* The R package installs were messed up. First install_geospatial.sh needs to be run first. Then other packages.
    - When I fixed the problem of installs going to /home (and then getting wiped out), I caused installs via install-r-packages.sh to go to source rather than binary.
    - There were a bunch of OHW R packages that I needed to add.
