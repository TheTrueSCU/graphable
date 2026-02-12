import sys


def app():
    """Main entry point that dispatches to rich or bare CLI."""
    # Check for --bare flag before anything else
    if "--bare" in sys.argv:
        # Remove --bare from argv so subparsers don't choke on it
        sys.argv.remove("--bare")
        from .bare_cli import run_bare

        run_bare()
        return

    try:
        # Try to use the rich CLI if dependencies are available
        from .rich_cli import app as rich_app

        rich_app()
    except ImportError:
        # Fallback to bare-bones CLI
        from .bare_cli import run_bare

        run_bare()


if __name__ == "__main__":
    app()
