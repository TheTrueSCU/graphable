from pathlib import Path


def is_path(source: str | Path) -> bool:
    """
    Check if the given source is likely a path to a file.

    Args:
        source: The source to check (string or Path object).

    Returns:
        bool: True if it's a Path object or a string that points to an existing file.
    """
    if isinstance(source, Path):
        return True

    if isinstance(source, str) and "\n" not in source and len(source) < 1024:
        try:
            return Path(source).exists()
        except OSError:
            pass

    return False
