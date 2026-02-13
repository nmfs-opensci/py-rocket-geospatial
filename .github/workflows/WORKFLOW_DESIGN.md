# CI/CD Workflow Design Documentation

## Overview

This document describes the restructured CI/CD workflow for py-rocket-geospatial-2 that ensures Docker images are only pushed after tests pass.

## Workflow Structure

### Build → Test → Push → Release

```
┌─────────┐
│  build  │ Builds Docker image, saves as artifact
└────┬────┘
     │
     ├─────────────────┬──────────────────┐
     │                 │                  │
     ▼                 ▼                  │
┌──────────┐    ┌─────────────┐          │ (skip_tests=true)
│test-     │    │test-        │          │
│python    │    │packages     │          │
└────┬─────┘    └──────┬──────┘          │
     │                 │                  │
     └────────┬────────┘                  │
              ▼                           ▼
         ┌────────┐◄──────────────────────┘
         │  push  │ Pushes to GHCR only if tests pass
         └───┬────┘
             │
             ▼
    ┌────────────────┐
    │create-release- │ Creates PR with pinned packages
    │pr              │
    └────────────────┘
```

## Job Details

### 1. `build` Job

**Purpose**: Build the Docker image without pushing it

**Key Steps**:
- Checkout code
- Check if tests should be skipped (based on workflow_dispatch input)
- Build Docker image with all required tags
- Save image as artifact using `docker save`
- Output image name, tag, and skip_tests flag

**Outputs**:
- `image_tag`: Short SHA of the commit (e.g., "abc1234")
- `image_name`: Full image name (e.g., "ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2")
- `skip_tests`: Boolean flag indicating if tests should be skipped

### 2. `test-python` Job

**Purpose**: Run Python notebook tests against the built image

**Depends On**: `build`

**Runs When**: `skip_tests == 'false'`

**Key Steps**:
- Download Docker image artifact
- Load image using `docker load`
- Configure NASA Earthdata credentials (if available)
- Run test notebook in the container
- Upload test results

**Validation**: Notebook must execute successfully without errors

### 3. `test-packages` Job

**Purpose**: Validate all specified packages are installed in the image

**Depends On**: `build`

**Runs When**: `skip_tests == 'false'`

**Key Steps**:
- Download Docker image artifact
- Load image
- Extract Python and R package lists from the container
- Validate against env-*.yml and install.R specifications
- Generate validation report (build.log)

**Outputs**:
- `validation_status`: "success" if all packages found, "failed" otherwise

**Validation**: All packages from:
- `conda-env/env-*.yml` files
- `install.R`
- Rocker scripts (install_geospatial.sh, install_tidyverse.sh)

Must be present in the container.

### 4. `push` Job

**Purpose**: Push the Docker image to GitHub Container Registry

**Depends On**: `build`, `test-python`, `test-packages`

**Runs When**:
- Tests are skipped (`skip_tests == 'true'`), OR
- Both `test-python` AND `test-packages` succeeded

**Key Steps**:
- Download Docker image artifact
- Load image
- Log in to GHCR
- Push image with all tags (short SHA, latest, version if available)

**Outputs**:
- `image_pushed`: "true" when push succeeds

### 5. `create-release-pr` Job

**Purpose**: Create a PR with pinned package versions and validation report

**Depends On**: `build`, `test-packages`, `push`

**Runs When**:
- Push succeeded (`image_pushed == 'true'`)
- Tests were NOT skipped (`skip_tests == 'false'`)

**Key Steps**:
- Download validation results (packages-python-pinned.yaml, packages-r-pinned.R, build.log)
- Create PR body with validation status and image information
- Commit changes to reproducibility/ directory
- Create PR assigned to @eeholmes

## Workflow Triggers

### Automatic Triggers (push to main)

Triggered when any of these files change on the `main` branch:
- `.github/actions/build-and-push/action.yml`
- `.github/workflows/build-and-push.yml`
- `Dockerfile`
- `conda-env/env-*.yml`
- `install.R`
- `apt.txt`
- `Desktop/**`

**Behavior**: Full build → test → push → release PR pipeline

### Manual Trigger (workflow_dispatch)

Can be triggered manually from GitHub Actions UI with options:

**Input Parameters**:
- `skip_tests` (boolean, default: false)
  - When `false`: Normal flow (build → test → push → release PR)
  - When `true`: Skip tests (build → push directly)

**When to Use `skip_tests: true`**:
- Debugging image build issues
- Testing Dockerfile changes that affect the build process
- Emergency hotfixes where tests are known to be broken for unrelated reasons

**⚠️ Important**: Using `skip_tests: true` bypasses all quality gates. Use with caution and only when necessary.

## Conditional Logic

### Test Jobs
```yaml
if: ${{ needs.build.outputs.skip_tests == 'false' }}
```
Tests only run when not explicitly skipped.

### Push Job
```yaml
if: |
  always() && 
  (needs.build.outputs.skip_tests == 'true' || 
   (needs.test-python.result == 'success' && needs.test-packages.result == 'success'))
```
Push happens if:
- Tests were skipped, OR
- Both test jobs succeeded

The `always()` ensures this evaluates even if upstream jobs were skipped.

### Release PR Job
```yaml
if: |
  always() && 
  needs.push.outputs.image_pushed == 'true' &&
  needs.build.outputs.skip_tests == 'false'
```
Release PR is created only when:
- Image was successfully pushed, AND
- Tests were run (not skipped)

## Artifact Management

**Docker Image Artifact**:
- Created in `build` job using `docker save`
- Compressed with gzip to reduce size
- Uploaded with 1-day retention
- Downloaded and loaded in subsequent jobs

**Validation Results Artifact**:
- Created in `test-packages` job
- Contains: packages-python-pinned.yaml, packages-r-pinned.R, build.log
- Downloaded in `create-release-pr` job
- Included in the PR

## Error Handling

### Test Failures

If either test job fails:
- Push job will not run
- Image remains untagged and unpushed
- Workflow fails, alerting maintainers
- Artifacts are retained for debugging

### Build Failures

If build job fails:
- No subsequent jobs run
- No artifacts created
- Workflow fails immediately

### Push Failures

If push job fails (after successful tests):
- Release PR job will not run
- Workflow fails
- May require manual intervention

## Comparison with Old Workflow

### Old Flow (workflow_run triggers)
```
Build & Push → (on completion) → Test Python
             → (on completion) → Pin Packages
```
**Problem**: Image already pushed even if tests fail

### New Flow (job dependencies)
```
Build → Test → Push (only if tests pass) → Release PR
```
**Benefit**: Image only pushed if quality gates pass

## Migration Notes

**Backward Compatibility**:
- `test-python.yml` still available for manual testing of existing images
- `pin-packages.yml` still available for manual package validation
- Both now only trigger via `workflow_dispatch` (no longer automatic)
- Main workflow is now `build-and-push.yml` with all steps integrated

**Breaking Changes**:
- Test and pin-packages workflows no longer auto-trigger via `workflow_run`
- If you were relying on automatic test runs after builds, update your process

## Future Enhancements

Potential improvements:
- [ ] Add GitHub release creation (not just PR)
- [ ] Include test result summaries in release notes
- [ ] Add notification mechanisms (Slack, email) on failures
- [ ] Implement version bumping automation
- [ ] Add performance benchmarking
- [ ] Cache Docker layers between builds for faster rebuilds
