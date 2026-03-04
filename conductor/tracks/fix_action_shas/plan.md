# Implementation Plan - Fix GitHub Action SHAs

This track addresses the `manifest unknown` errors in GitHub Actions by correcting invalid SHA-1 pins.

## Goals

- [x] Update `publish.yml` with correct SHAs.
- [x] Update `ci.yml` with correct SHAs.
- [x] Update `docs.yml` with correct SHAs.

## Correct SHAs (Verified via git ls-remote)

- `actions/checkout@v4.2.2`: `11bd71901bbe5b1630ceea73d27597364c9af683`
- `astral-sh/setup-uv@v5.2.2`: `4db96194c378173c656ce18a155ffc14a9fc4355`
- `actions/setup-python@v5.4.0`: `42375524e23c412d93fb67b49958b491fce71c38`
- `pypa/gh-action-pypi-publish@v1.12.4`: `7f25271a4aa483500f742f9492b2ab5648d61011`
- `actions/setup-node@v4.2.0`: `1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a`
- `actions/upload-pages-artifact@v3.0.1`: `56afc609e74202658d3ffba0e8f6dda462b719fa`
- `actions/deploy-pages@v4.0.5`: `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e`
- `extractions/setup-just@v2.0.0`: `dd310ad5a97d8e7b41793f8ef055398d51ad4de6`
