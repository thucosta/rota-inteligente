import argparse
import csv
import json
from functools import cache
from math import isfinite
from pathlib import Path
from statistics import median
from time import perf_counter

from .routing import City, Street, kmeans, optimize
from .visual import draw_map


def rows(folder, filename):
    with (folder / filename).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load(folder, scenario, metric, depot):
    points = {}
    for row in rows(folder, "points.csv"):
        node = row["id"]
        position = float(row["x"]), float(row["y"])
        if not node or node in points or not all(map(isfinite, position)):
            raise ValueError(f"Ponto inválido ou repetido: {node}")
        points[node] = position
    streets = {node: [] for node in points}
    arcs = set()
    for row in rows(folder, "streets.csv"):
        origin, target = row["origin"], row["destination"]
        km, minutes = float(row["km"]), float(row["minutes"])
        if origin not in points or target not in points or (origin, target) in arcs:
            raise ValueError(f"Rua inválida ou repetida: {origin} → {target}")
        if not all(isfinite(value) and value > 0 for value in (km, minutes)):
            raise ValueError(f"Peso inválido: {origin} → {target}")
        streets[origin].append(Street(target, km, minutes))
        arcs.add((origin, target))
    orders = [r["node"] for r in rows(folder, "orders.csv") if r["scenario"] == scenario]
    if depot not in points or not orders or set(orders) - points.keys() or depot in orders:
        raise ValueError("Verifique a base, o cenário e os pontos de entrega")
    if len(set(orders)) != len(orders):
        raise ValueError("Consolide pedidos do mesmo endereço em uma parada por cenário")
    return City(points, streets, metric), orders


def evaluate(city, orders, depot, k):
    @cache
    def leg(start, goal):
        return city.shortest(start, goal)

    def cost(start, goal):
        return getattr(leg(start, goal), city.metric)

    manual = [orders[index::k] for index in range(k)]
    clustered = kmeans(city.points, orders, k)
    strategies = {
        "ordem_chegada": [(depot, *group, depot) for group in manual],
        "mesmos_grupos_otimizados": [optimize(group, depot, cost) for group in manual],
        "kmeans_otimizado": [optimize(group, depot, cost) for group in clustered],
    }
    result = {}
    for strategy, routes in strategies.items():
        details = []
        for route in routes:
            legs = [leg(start, end) for start, end in zip(route, route[1:])]
            details.append({
                "paradas": route[1:-1],
                "caminho": [depot, *(node for item in legs for node in item.nodes[1:])],
                "km": round(sum(item.km for item in legs), 4),
                "minutos": round(sum(item.minutes for item in legs), 4),
            })
        result[strategy] = {
            "km_total": round(sum(route["km"] for route in details), 4),
            "minutos_totais": round(sum(route["minutos"] for route in details), 4),
            "minutos_maior_rota": max(route["minutos"] for route in details),
            "rotas": details,
        }
    return result


def benchmark(city, stops):
    # Same directed origin/destination pairs for both searches, with fresh runs.
    pairs = [(a, b) for a in stops for b in stops if a != b]
    output = {}
    for name, use_heuristic in (("astar", True), ("dijkstra", False)):
        samples = []
        for _ in range(7):
            start = perf_counter()
            paths = [city.shortest(a, b, use_heuristic=use_heuristic) for a, b in pairs]
            samples.append((perf_counter() - start) * 1000)
        output[name] = {
            "pares": len(pairs),
            "expansoes": sum(path.expanded for path in paths),
            "mediana_ms": round(median(samples), 3),
        }
    return output


def main():
    parser = argparse.ArgumentParser(description="Roteirização da Sabor Express")
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--scenario", default="pico")
    parser.add_argument("--couriers", type=int, default=2)
    parser.add_argument("--metric", choices=("km", "minutes"), default="minutes")
    parser.add_argument("--depot", default="BASE")
    args = parser.parse_args()
    try:
        city, orders = load(args.data, args.scenario, args.metric, args.depot)
        if not 1 <= args.couriers <= len(orders):
            raise ValueError("Informe de 1 até o número de paradas como quantidade de entregadores")
        result = evaluate(city, orders, args.depot, args.couriers)
        report = {
            "cenario": args.scenario,
            "criterio": args.metric,
            "entregadores": args.couriers,
            "entregas": len(orders),
            "estrategias": result,
            "buscas": benchmark(city, [args.depot, *orders]),
        }
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "resultados.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        draw_map(city, args.depot, result["kmeans_otimizado"]["rotas"], args.output / "grafo.svg")
    except (OSError, KeyError, ValueError) as error:
        parser.error(str(error))
    for strategy, totals in result.items():
        print(f'{strategy:28} {totals["km_total"]:7.2f} km  '
              f'{totals["minutos_totais"]:7.2f} min  '
              f'rota mais longa: {totals["minutos_maior_rota"]:.2f} min')
    print(f"Resultados em {args.output}")


if __name__ == "__main__":
    main()
