"""Stable sparse graph utilities for certified partial rankings."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Any


Edge = tuple[str, str]


def _nodes(edges: Iterable[Edge], extra: Iterable[str] = ()) -> list[str]:
    return sorted(set(extra) | {node for edge in edges for node in edge})


def adjacency(edges: Iterable[Edge], nodes: Iterable[str] = ()) -> dict[str, set[str]]:
    edge_list = list(edges)
    graph: dict[str, set[str]] = {node: set() for node in _nodes(edge_list, nodes)}
    for source, target in edge_list:
        if source == target:
            raise ValueError("self edges are not permitted")
        graph[source].add(target)
    return graph


def transitive_closure(edges: Iterable[Edge], nodes: Iterable[str] = ()) -> list[Edge]:
    graph = adjacency(edges, nodes)
    closure: set[Edge] = set()
    for source in graph:
        pending = list(graph[source])
        visited: set[str] = set()
        while pending:
            target = pending.pop()
            if target in visited:
                continue
            visited.add(target)
            closure.add((source, target))
            pending.extend(graph[target] - visited)
    return sorted(closure)


def strongly_connected_components(edges: Iterable[Edge], nodes: Iterable[str] = ()) -> list[list[str]]:
    graph = adjacency(edges, nodes)
    reverse: dict[str, set[str]] = {node: set() for node in graph}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].add(source)
    visited: set[str] = set()
    order: list[str] = []
    for start in sorted(graph):
        if start in visited:
            continue
        stack: list[tuple[str, bool]] = [(start, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded:
                order.append(node)
                continue
            if node in visited:
                continue
            visited.add(node)
            stack.append((node, True))
            stack.extend((child, False) for child in sorted(graph[node], reverse=True) if child not in visited)
    components: list[list[str]] = []
    visited.clear()
    for start in reversed(order):
        if start in visited:
            continue
        component: list[str] = []
        pending = [start]
        visited.add(start)
        while pending:
            node = pending.pop()
            component.append(node)
            for child in sorted(reverse[node], reverse=True):
                if child not in visited:
                    visited.add(child)
                    pending.append(child)
        components.append(sorted(component))
    return sorted(components, key=lambda component: (component[0], len(component)))


def transitive_reduction(edges: Iterable[Edge], nodes: Iterable[str] = ()) -> list[Edge]:
    edge_list = sorted(set(edges))
    if any(len(component) > 1 for component in strongly_connected_components(edge_list, nodes)):
        raise ValueError("transitive reduction requires a directed acyclic graph")
    graph = adjacency(edge_list, nodes)
    reduced: list[Edge] = []
    for source, target in edge_list:
        pending = list(graph[source] - {target})
        visited: set[str] = set()
        reachable = False
        while pending and not reachable:
            node = pending.pop()
            if node == target:
                reachable = True
                break
            if node not in visited:
                visited.add(node)
                pending.extend(graph[node] - visited)
        if not reachable:
            reduced.append((source, target))
    return reduced


def incomparability_graph(edges: Iterable[Edge], nodes: Iterable[str]) -> list[Edge]:
    node_list = sorted(set(nodes))
    closure = set(transitive_closure(edges, node_list))
    return [
        (left, right)
        for index, left in enumerate(node_list)
        for right in node_list[index + 1 :]
        if (left, right) not in closure and (right, left) not in closure
    ]


def connected_components(edges: Iterable[Edge], nodes: Iterable[str]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        graph[node]
    for left, right in edges:
        graph[left].add(right)
        graph[right].add(left)
    components: list[list[str]] = []
    unseen = set(graph)
    while unseen:
        start = min(unseen)
        component: list[str] = []
        queue = deque([start])
        unseen.remove(start)
        while queue:
            node = queue.popleft()
            component.append(node)
            for neighbor in sorted(graph[node]):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def graph_payload(
    nodes: list[str],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    directed = sorted(
        (str(edge["source"]), str(edge["target"]))
        for edge in edges
        if edge.get("decision") in {"A_BETTER", "B_BETTER"}
    )
    components = strongly_connected_components(directed, nodes)
    cyclic = [component for component in components if len(component) > 1]
    reduction = [] if cyclic else transitive_reduction(directed, nodes)
    return {
        "schema_version": "certgen.icml2027.ranking_graph.v1",
        "nodes": sorted(nodes),
        "edges": sorted(edges, key=lambda edge: (str(edge["source"]), str(edge["target"]), str(edge.get("feature_space", "")))),
        "transitive_closure": transitive_closure(directed, nodes),
        "transitive_reduction": reduction,
        "strongly_connected_components": components,
        "cycles": cyclic,
        "incomparability_edges": incomparability_graph(directed, nodes),
        "connected_components": connected_components(directed, nodes),
        "claim_allowed": False,
    }
