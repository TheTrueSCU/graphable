import re
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


def extract_checksum(source: str | Path) -> str | None:
    """
    Extract a blake2b checksum from the first few lines of a source.
    Looks for the pattern 'blake2b: <hash>'.

    Args:
        source: The source to check (string or Path object).

    Returns:
        str | None: The hash if found, otherwise None.
    """
    content = ""
    if is_path(source):
        try:
            # Read only the first 1KB to find comments
            with open(source, "r") as f:
                content = f.read(1024)
        except Exception:
            return None
    else:
        content = str(source)[:1024]

    # Match blake2b: followed by hex chars (usually 128 for blake2b)
    match = re.search(r"blake2b:\s*([a-fA-F0-9]+)", content)
    if match:
        return match.group(1)

    return None
