from dataclasses import dataclass
from functools import cache
from heapq import heappop, heappush
from math import dist, inf
from random import Random
from statistics import mean


@dataclass(frozen=True)
class Street:
    target: str
    km: float
    minutes: float


@dataclass(frozen=True)
class Leg:
    nodes: tuple[str, ...]
    km: float
    minutes: float
    expanded: int


class City:
    def __init__(self, points, streets, metric):
        self.points = points
        self.streets = streets
        self.metric = metric
        # Each edge costs at least scale times its straight-line length.
        self.scale = min(
            (getattr(edge, metric) / distance
             for node, edges in streets.items() for edge in edges
             if (distance := dist(points[node], points[edge.target])) > 0),
            default=0,
        )

    def shortest(self, start, goal, *, use_heuristic=True):
        def estimate(node):
            return self.scale * dist(self.points[node], self.points[goal]) if use_heuristic else 0

        queue = [(estimate(start), 0, start)]
        best = {start: 0}
        predecessors = {}
        expanded = 0
        while queue:
            _, cost, node = heappop(queue)
            if cost != best[node]:
                continue
            expanded += 1
            if node == goal:
                path = [goal]
                km = minutes = 0
                while path[-1] != start:
                    previous, edge = predecessors[path[-1]]
                    path.append(previous)
                    km += edge.km
                    minutes += edge.minutes
                return Leg(tuple(reversed(path)), km, minutes, expanded)
            for edge in self.streets[node]:
                candidate = cost + getattr(edge, self.metric)
                if candidate < best.get(edge.target, inf):
                    best[edge.target] = candidate
                    predecessors[edge.target] = node, edge
                    heappush(queue, (candidate + estimate(edge.target), candidate, edge.target))
        raise ValueError(f"Sem caminho de {start} a {goal}")


def kmeans(points, orders, k, seed=42):
    """Lloyd clustering with deterministic initialization and nonempty groups."""
    centers = [points[node] for node in Random(seed).sample(sorted(orders), k)]
    previous = None
    for _ in range(100):
        groups = [[] for _ in centers]
        for node in orders:
            index = min(range(k), key=lambda i: dist(points[node], centers[i]))
            groups[index].append(node)
        for group in groups:
            if not group:
                donor = max(range(k), key=lambda i: len(groups[i]))
                node = max(groups[donor], key=lambda n: dist(points[n], centers[donor]))
                groups[donor].remove(node)
                group.append(node)
        if groups == previous:
            break
        previous = groups
        centers = [tuple(map(mean, zip(*(points[n] for n in group)))) for group in groups]
    return groups


def optimize(stops, depot, cost):
    """Return a depot-to-depot visit order for the given group."""
    if len(stops) > 10:
        remaining = set(stops)
        route = [depot]
        while remaining:
            node = min(remaining, key=lambda n: (cost(route[-1], n), n))
            remaining.remove(node)
            route.append(node)
        return (*route, depot)

    @cache
    def best(node, remaining):
        if not remaining:
            return cost(node, depot), (depot,)
        candidates = []
        for index, target in enumerate(remaining):
            suffix_cost, suffix = best(target, remaining[:index] + remaining[index + 1:])
            candidates.append((cost(node, target) + suffix_cost, (target, *suffix)))
        return min(candidates)

    result = (depot, *best(depot, tuple(sorted(stops)))[1])
    best.cache_clear()
    return result
