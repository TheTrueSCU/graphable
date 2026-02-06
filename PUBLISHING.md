# Publishing Guide

This guide details how to publish `graphable` to PyPI and update the documentation.

## One-Time Setup

### 1. Configure PyPI Trusted Publishing

This project uses [Trusted Publishing](https://docs.pypi.org/trusted-publishing/) (OIDC) to publish to PyPI without long-lived API tokens.

1.  Go to [PyPI](https://pypi.org/) and log in.
2.  Go to **Publishing** (or create the project if it doesn't exist yet).
3.  Add a new **GitHub** publisher.
    *   **Owner**: (Your GitHub Username/Org, e.g., `TheTrueSCU`)
    *   **Repository**: `graphable`
    *   **Workflow name**: `publish.yml`
    *   **Environment name**: `pypi`
4.  Add the publisher.

### 2. Configure GitHub Pages

1.  Go to your GitHub repository **Settings**.
2.  Navigate to **Pages** (in the sidebar).
3.  Under **Build and deployment** > **Source**, select **GitHub Actions**.
4.  (Optional) If you have a custom domain, configure it here.

## Releasing a New Version

### 1. Update Version

Edit `pyproject.toml` and bump the version number:

```toml
[project]
name = "graphable"
version = "0.2.0"  # <--- Update this
```

### 2. Commit and Push

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### 3. Create a Release

1.  Go to the **Releases** section of your GitHub repository.
2.  Click **Draft a new release**.
3.  **Choose a tag**: Create a new tag matching your version (e.g., `v0.2.0`).
4.  **Title**: "Version 0.2.0" (or similar).
5.  **Description**: Describe the changes in this release.
6.  Click **Publish release**.

### Automation Results

*   **PyPI**: The `publish.yml` workflow will trigger, build the package, and upload it to PyPI.
*   **Documentation**: The `docs.yml` workflow will trigger on the push to `main` (and can also be manually run), building the docs and deploying them to GitHub Pages.
