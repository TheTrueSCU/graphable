from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .graph import Graph

# Define types for parsers and exporters
ParserFnc = Callable[..., "Graph[Any]"]
ExporterFnc = Callable[["Graph[Any]", Any], None]
CreatorFnc = Callable[["Graph[Any]", Any], str]

# Registry for parsers (extension -> function)
PARSERS: dict[str, ParserFnc] = {}

# Registry for exporters (extension -> function)
EXPORTERS: dict[str, ExporterFnc] = {}

# Registry for creators (function that returns string instead of writing to file)
# Maps an export function to its corresponding create function
CREATOR_MAP: dict[ExporterFnc, CreatorFnc] = {}


def register_parser(extension: str | list[str]):
    def decorator(fnc: ParserFnc):
        exts = [extension] if isinstance(extension, str) else extension
        for ext in exts:
            PARSERS[ext.lower()] = fnc
        return fnc

    return decorator


def register_view(extension: str | list[str], creator_fnc: CreatorFnc | None = None):
    def decorator(fnc: ExporterFnc):
        exts = [extension] if isinstance(extension, str) else extension
        for ext in exts:
            EXPORTERS[ext.lower()] = fnc
        if creator_fnc:
            CREATOR_MAP[fnc] = creator_fnc
        return fnc

    return decorator
