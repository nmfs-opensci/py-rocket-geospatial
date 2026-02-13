# Python Tests for py-rocket-geospatial-2

This directory contains Jupyter notebooks that test the Python environment in the Docker image.

## How Tests Work

1. **Trigger**: The test workflow (`.github/workflows/test-python.yml`) runs automatically after a successful build-and-push.yml workflow
2. **Execution**: Each notebook is executed inside the Docker container using `jupyter nbconvert --execute`
3. **Results**: Test outputs are saved as artifacts and can be downloaded from the GitHub Actions run

## Running Tests Locally

You can run the tests locally using the Docker image:

```bash
# Pull the latest image
docker pull ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest

# Run a test notebook
docker run --rm \
  -v "$PWD/tests:/tests" \
  ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest \
  bash -c "jupyter nbconvert --to notebook --execute /tests/test-python-xarray.ipynb --output /tests/test-python-xarray-output.ipynb"
```

## Current Tests

### test-python-xarray.ipynb
Tests that the Python environment can:
- Import xarray
- Open remote NetCDF files using h5netcdf engine
- Read data from NMFS ODP storage

## Adding New Tests

To add a new test:

1. Create a new Jupyter notebook in this directory (e.g., `test-python-newfeature.ipynb`)
2. Write test code with assertions to verify functionality
3. Add a step to `.github/workflows/test-python.yml` to run the new notebook
4. Update this README with a description of the new test

Each test notebook should:
- Be self-contained and runnable in isolation
- Include markdown cells explaining what is being tested
- Use assertions to verify expected behavior
- Print clear success/failure messages
