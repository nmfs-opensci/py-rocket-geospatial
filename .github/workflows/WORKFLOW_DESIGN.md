# CI/CD Workflow Design Documentation

## Overview

This document describes the restructured CI/CD workflow for py-rocket-geospatial-2 that ensures Docker images are only pushed after tests pass.

## Workflow Structure

### Single Job: Build → Test → Push (in one runner)

```
┌──────────────────────────────────────────────┐
│         build-test-push (single job)         │
│                                              │
│  1. Build Docker image (tagged with SHA)    │
│  2. Run Python notebook tests (optional)    │
│  3. Run package validation (optional)       │
│  4. Push image to GHCR (if tests pass)      │
│                                              │
│  (skip_tests=true bypasses steps 2-3)       │
└─────────────────┬────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │create-release- │ Creates PR with pinned packages
         │pr              │
         └────────────────┘
```

**Key Design Change**: Consolidated from 5 jobs to 2 jobs to avoid artifact transfer overhead. The Docker image (7GB+ compressed) stays in the build runner's local Docker cache, avoiding the need to save/load via artifacts.

## Job Details

### 1. `build-test-push` Job

**Purpose**: Build, test, and push the Docker image in a single job

**Key Steps**:
- Checkout code
- Check if tests should be skipped (based on workflow_dispatch input)
- Log in to GHCR
- Build Docker image with all required tags (stays in local Docker cache)
- **Run Python notebook tests** (if skip_tests=false)
- **Run package validation** (if skip_tests=false)
- **Push image to GHCR** (always, but only after tests pass if not skipped)
- Upload small artifacts (test results, validation results) with 7-day retention

**Outputs**:
- `image_tag`: Short SHA of the commit (e.g., "abc1234")
- `image_name`: Full image name (e.g., "ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2")
- `image_pushed`: "true" when push succeeds
- `validation_status`: "success" if all packages found, "failed" otherwise

**Test Execution** (if skip_tests=false):
- Configure NASA Earthdata credentials (if available)
- Run Python notebook test (test-python-xarray.ipynb)
- Extract and validate Python packages from conda environment
- Extract and validate R packages from site-library
- Generate validation report (build.log)

**Validation**: 
- Notebook must execute successfully
- All packages from env-*.yml, install.R, and Rocker scripts must be present

**Artifacts Uploaded** (7-day retention):
- test-results: Executed notebook output
- validation-results: Pinned packages and build.log

### 2. `create-release-pr` Job

**Purpose**: Create a PR with pinned package versions and validation report

**Depends On**: `build-test-push`

**Runs When**:
- Main job succeeded (`result == 'success'`)
- Image was pushed (`image_pushed == 'true'`)

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

**Small Artifacts Only** (7-day retention):
- test-results: Executed notebook output (~few MB)
- validation-results: Pinned packages and build.log (~few MB)

**No Docker Image Artifact**: The Docker image (~7GB compressed) stays in the build runner's local Docker cache. This avoids the need to save/load the image between jobs, which would be impractical for large images and could hit GitHub's artifact size limits.

## Error Handling

### Test Failures

If any test step fails in the `build-test-push` job:
- Push step will not execute (job fails before reaching it)
- Image remains untagged and unpushed
- Workflow fails, alerting maintainers
- Small artifacts (test results, validation) are retained for debugging

### Build Failures

If build step fails:
- No test or push steps run
- Workflow fails immediately

### Push Failures

If push step fails (after successful tests):
- Release PR job will not run
- Workflow fails
- May require manual intervention

## Comparison with Previous Approaches

### Original Flow (workflow_run triggers)
```
Build & Push → (on completion) → Test Python
             → (on completion) → Pin Packages
```
**Problem**: Image already pushed even if tests fail

### Previous Multi-Job Flow (artifact transfer)
```
Build (save artifact) → Test (load artifact) → Push (load artifact)
```
**Problem**: 7GB compressed image is too large for efficient artifact transfer

### Current Flow (single job)
```
Build → Test → Push (all in one runner, image stays in Docker cache)
         ↓
    Release PR (separate job, uses small artifacts only)
```
**Benefit**: 
- Image only pushed if quality gates pass
- No artifact transfer overhead for large images
- Simpler workflow with fewer jobs
- More robust for huge container images

## Migration Notes

**Backward Compatibility**:
- `test-python.yml` still available for manual testing of existing images
- `pin-packages.yml` still available for manual package validation
- Both now only trigger via `workflow_dispatch` (no longer automatic)
- Main workflow is now `build-and-push.yml` with all steps integrated in a single job

**Breaking Changes**:
- Test and pin-packages workflows no longer auto-trigger via `workflow_run`
- Reduced from 5 jobs to 2 jobs for efficiency

## Future Enhancements

Potential improvements:
- [ ] Add GitHub release creation (not just PR)
- [ ] Include test result summaries in release notes
- [ ] Add notification mechanisms (Slack, email) on failures
- [ ] Implement version bumping automation
- [ ] Add performance benchmarking
- [ ] Cache Docker layers between builds for faster rebuilds
