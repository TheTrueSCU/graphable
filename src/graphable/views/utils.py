def wrap_with_checksum(content: str, checksum: str, extension: str) -> str:
    """
    Prepend a checksum as a comment to the content based on file extension.

    Args:
        content: The original content string.
        checksum: The blake2b hash to embed.
        extension: The file extension (e.g., '.json', '.yaml').

    Returns:
        str: The content with the checksum comment prepended.
    """
    prefix = f"blake2b: {checksum}"

    ext = extension.lower()

    if ext == ".graphml" or ext == ".html" or ext == ".xml":
        comment = f"<!-- {prefix} -->"
    elif ext in (".yaml", ".yml", ".toml", ".txt", ".ascii", ".csv"):
        comment = f"# {prefix}"
    elif ext in (".dot", ".gv", ".d2"):
        comment = f"// {prefix}"
    elif ext == ".mmd" or ext == ".mermaid":
        comment = f"%% {prefix}"
    elif ext == ".puml":
        comment = f"' {prefix}"
    elif ext == ".tex":
        comment = f"% {prefix}"
    elif ext == ".json":
        import json

        try:
            # Parse the rendered JSON string back to a dict
            data = json.loads(content)
            # Wrap it in a higher-order dict
            wrapped_data = {"checksum": prefix, "graph": data}
            # Return as a formatted JSON string
            return json.dumps(wrapped_data, indent=2)
        except Exception:
            # Fallback if content isn't valid JSON for some reason
            return f"# {prefix}\n{content}"
    else:
        comment = f"# {prefix}"

    return f"{comment}\n{content}"
