# Implementation Plan - Fix GitHub Action SHAs

This track addresses the `manifest unknown` errors in GitHub Actions by correcting invalid SHA-1 pins.

## Goals

- [x] Update `publish.yml` with correct SHAs.
- [x] Update `ci.yml` with correct SHAs.
- [x] Update `docs.yml` with correct SHAs.

## Correct SHAs (as of 2026-03-04)

- `actions/checkout@v4`: `eef61427696e92600c02884c12c84b55296d527b`
- `astral-sh/setup-uv@v5`: `f986551039737c51bdec33ef4f453f3d35fa28d5`
- `actions/setup-python@v5`: `42375524e23c412d93fb67b49958b491fbbbd4ee`
- `pypa/gh-action-pypi-publish@v1.12.4`: `63304f351496d56475485f88475f795f1c033de1`
- `actions/setup-node@v4`: `39225597fd64c39d91223a498993f7734fdec560`
- `actions/upload-pages-artifact@v3`: `25357303d001614207908c691f1a50a11e74f9d0`
- `actions/deploy-pages@v4`: `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`
- `extractions/setup-just@v2`: `dd310ad5a97d8e7b41793f8ef055398d51ad4de6` (Verified)
