from pathlib import Path
from unittest.mock import mock_open, patch

from graphable.views.markdown import export_markdown_wrapped, wrap_in_markdown


class TestMarkdown:
    def test_wrap_in_markdown(self):
        content = "graph definition"
        wrapped = wrap_in_markdown(content, "mermaid")

        assert "```mermaid" in wrapped
        assert content in wrapped
        assert "```" in wrapped

    def test_export_markdown_wrapped(self):
        content = "content"
        output_path = Path("output.md")

        with patch("builtins.open", mock_open()) as mock_file:
            export_markdown_wrapped(content, "d2", output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
