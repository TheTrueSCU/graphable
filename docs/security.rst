Security Policy
===============

``graphable`` is committed to ensuring the security and integrity of your graph data and the systems that process it. This document outlines our security model and the measures we take to protect against common vulnerabilities.

Security Model
--------------

The library processes external input in two primary ways:
1. **Parsers**: Loading graph structures from JSON, YAML, TOML, CSV, and GraphML.
2. **Exporters**: Generating visual or data-based representations.

We treat all external input as untrusted and apply strict sanitization and validation at these boundaries.

Recent Hardening
----------------

As of version 0.6.0, the following security enhancements have been implemented:

*   **Secure XML Parsing**: The GraphML parser now uses ``defusedxml`` to prevent XML External Entity (XXE) processing and expansion attacks.
*   **Command Injection Mitigation**: Visualization exports that rely on external CLI tools (like Mermaid) use strict argument quoting (``shlex.quote``) to prevent arbitrary command execution via malformed file paths.
*   **Cross-Site Scripting (XSS) Protection**:
    *   Standalone HTML visualizations now HTML-escape all user-provided titles and labels.
    *   JSON data embedded in script blocks is sanitized to prevent breaking out of the ``<script>`` context.
    *   The ``serve`` command's live-reload server escapes exception messages before reflecting them in error pages.
*   **Injection Protection**: The Graphviz DOT exporter escapes double quotes and backslashes in node identifiers and attributes to prevent DOT injection attacks.

Reporting a Vulnerability
-------------------------

If you discover a security vulnerability within this project, please report it privately. Do not use the public GitHub issue tracker.

Please email the maintainer directly at: ``dopplereffect.us@gmail.com``

We will acknowledge your report within 48 hours and provide a timeline for resolution.
