# Git Flow Branching Strategy

This project follows the standard **Git Flow** branching model to manage releases and feature integrations.

## Branch Classification

### 1. `main`
- Contains only production-ready, verified code.
- Merges to `main` are made strictly via Release or Hotfix branches and require sign-off.
- Every commit on `main` is tagged with a version number (e.g. `v0.1.0`).

### 2. `develop`
- The main development and integration branch.
- Reflects the latest completed development changes for the next release.
- Nightly integration tests and automated builds pull from this branch.

### 3. Feature Branches (`feature/*`)
- Created for specific features or issue resolutions.
- Branch off from: `develop`
- Merge back into: `develop`
- Named logically:
  - `feature/chat`: AI chat interface and LLM integration
  - `feature/network`: Entity association network rendering (React Flow)
  - `feature/analytics`: Trend analysis and predictive modeling
  - `feature/maps`: Geospatial mapping layers (Leaflet)
  - `feature/reports`: PDF layout compiler and reporting engines

### 4. Release Branches (`release/*`)
- Created when a release is near completion for staging tests.
- Branch off from: `develop`
- Merge back into: `main` and `develop`

### 5. Hotfix Branches (`hotfix/*`)
- Used for quick patches to production bugs.
- Branch off from: `main`
- Merge back into: `main` and `develop`
