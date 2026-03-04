from logging import getLogger

from ..graph import Graph

logger = getLogger(__name__)


def to_networkx(graph: Graph):
    """
    Convert a graphable.Graph to a networkx.DiGraph.
    Requires 'networkx' to be installed.

    Args:
        graph (Graph): The graph to convert.

    Returns:
        networkx.DiGraph: The converted directed graph.

    Raises:
        ImportError: If networkx is not installed.
    """
    try:
        import networkx as nx
    except ImportError as e:
        logger.error(
            "NetworkX is not installed. Run 'pip install networkx' to use this feature."
        )
        raise ImportError(
            "networkx is required for this feature. "
            "Install it with 'pip install networkx' or 'uv add networkx'."
        ) from e

    logger.debug("Converting graph to NetworkX DiGraph.")
    dg = nx.DiGraph()

    for node in graph.topological_order():
        # Add node with metadata
        dg.add_node(str(node.reference), reference=node.reference, tags=list(node.tags))

        # Add edges
        for dependent, attrs in graph.internal_dependents(node):
            dg.add_edge(str(node.reference), str(dependent.reference), **attrs)

    return dg
