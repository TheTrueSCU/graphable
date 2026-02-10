from logging import getLogger
from pathlib import Path

logger = getLogger(__name__)


def wrap_in_markdown(content: str, language: str) -> str:
    """
    Wrap a string in a Markdown code block.

    Args:
        content (str): The content to wrap.
        language (str): The language identifier for the code block (e.g., 'mermaid', 'd2').

    Returns:
        str: The Markdown-wrapped content.
    """
    return f"```{language}\n{content}\n```"


def export_markdown_wrapped(content: str, language: str, output: Path) -> None:
    """
    Export content wrapped in Markdown to a file.

    Args:
        content (str): The content to wrap and export.
        language (str): The language identifier.
        output (Path): The output file path.
    """
    logger.info(f"Exporting Markdown-wrapped content to: {output}")
    with open(output, "w+") as f:
        f.write(wrap_in_markdown(content, language))
