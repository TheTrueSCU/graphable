from shutil import which
from typing import Callable


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


def detect_engine() -> str:
    """
    Detect the available visualization engine based on system PATH.
    Priority: Mermaid -> Graphviz -> D2 -> PlantUML.

    Returns:
        str: The name of the detected engine.

    Raises:
        RuntimeError: If no engine is found.
    """
    engines = {
        "mermaid": "mmdc",
        "graphviz": "dot",
        "d2": "d2",
        "plantuml": "plantuml",
    }

    for engine, executable in engines.items():
        if which(executable):
            return engine

    raise RuntimeError(
        "No rendering engine found on PATH. "
        "Please install one of: mermaid-cli, graphviz, d2, or plantuml."
    )


def get_image_exporter(engine: str | None = None) -> Callable[..., None]:
    """
    Get the appropriate image exporter based on the engine name or auto-detection.

    Args:
        engine: Optional engine name (e.g., 'mermaid', 'graphviz').

    Returns:
        Callable: An export function that takes (graph, output_path, **kwargs).
    """
    from ..enums import Engine

    if engine is None:
        engine_val = detect_engine()
    else:
        # Normalize engine name
        engine_val = engine.value if isinstance(engine, Engine) else engine.lower()

    if engine_val == Engine.MERMAID:
        from .mermaid import export_topology_mermaid_image as exporter
    elif engine_val == Engine.GRAPHVIZ:
        from .graphviz import export_topology_graphviz_image as exporter
    elif engine_val == Engine.D2:
        from .d2 import export_topology_d2_image as exporter
    elif engine_val == Engine.PLANTUML:
        from .plantuml import export_topology_plantuml_image as exporter
    else:
        raise ValueError(f"Unknown rendering engine: {engine_val}")

    return exporter
