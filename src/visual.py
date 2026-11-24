from html import escape
from math import hypot


def draw_map(city, depot, routes, destination):
    xs, ys = zip(*city.points.values())
    scale = min(640 / max(max(xs) - min(xs), 1), 295 / max(max(ys) - min(ys), 1))
    points = {
        node: (80 + (x - min(xs)) * scale, 110 + (y - min(ys)) * scale)
        for node, (x, y) in city.points.items()
    }
    colors = ("#0369a1", "#b45309", "#047857", "#7e22ce", "#be123c")
    body = [
        '<rect width="800" height="480" fill="#f8fafc"/>',
        '<text x="40" y="46" font-size="26" font-weight="700">Rede de entregas da Sabor Express</text>',
        '<text x="40" y="73" font-size="15">Cinza = rua disponível · seta = sentido único · números = entregadores</text>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 Z" fill="#475569"/></marker></defs>',
    ]
    arcs = {(node, edge.target) for node, edges in city.streets.items() for edge in edges}
    for node, target in sorted(arcs):
        x1, y1 = points[node]
        x2, y2 = points[target]
        body.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#94a3b8" stroke-width="2"/>')
    assignments = {}
    for index, route in enumerate(routes):
        color = colors[index % len(colors)]
        offsets = (index - (len(routes) - 1) / 2) * 5
        for node in route["paradas"]:
            assignments[node] = (color, index + 1)
        for a, b in zip(route["caminho"], route["caminho"][1:]):
            x1, y1 = points[a]
            x2, y2 = points[b]
            length = hypot(x2 - x1, y2 - y1)
            if length:
                direction = 1 if a < b else -1
                dx = direction * (y1 - y2) * offsets / length
                dy = direction * (x2 - x1) * offsets / length
                body.append(f'<path d="M{x1+dx},{y1+dy} L{x2+dx},{y2+dy}" '
                            f'stroke="{color}" stroke-width="4"/>')
    for a, b in sorted(arcs):
        if (b, a) not in arcs:
            x1, y1 = points[a]
            x2, y2 = points[b]
            body.append(f'<path d="M{(x1+x2)/2},{(y1+y2)/2} L{0.35*x1+0.65*x2},{0.35*y1+0.65*y2}" '
                        'stroke="#475569" marker-end="url(#arrow)"/>')
    for node, (x, y) in points.items():
        color, number = assignments.get(node, ("#334155", ""))
        radius = 11 if number or node == depot else 5
        body.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')
        if number:
            body.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="11" fill="white">{number}</text>')
        body.append(f'<text x="{x+14}" y="{y-12}" font-size="14">{escape(node)}</text>')
    destination.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" role="img" '
        'font-family="system-ui,sans-serif" fill="#0f172a"><title>Grafo das rotas agrupadas</title>\n'
        + "\n".join(body) + "\n</svg>\n",
        encoding="utf-8",
    )
