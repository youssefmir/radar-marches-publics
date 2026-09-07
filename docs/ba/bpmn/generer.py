"""Génère les diagrammes BPMN 2.0 (AS-IS / TO-BE) de la veille et de la réponse aux appels d'offres.

Produit pour chaque processus un fichier .bpmn (BPMN 2.0 avec coordonnées DI, ouvrable dans
bpmn.io / Camunda Modeler) et un rendu .svg équivalent pour la lecture sur GitHub.
Usage : python docs/ba/bpmn/generer.py
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent
LANE_H, X0, STEP, W, H = 150, 150, 170, 130, 64

# (id, type, libellé, couloir, colonne) ; types : start, end, task, gateway, auto (tâche outillée)
PROCESSES = {
    "as-is": {
        "titre": "AS-IS — Veille et réponse aux appels d'offres dans une PME (sans outil)",
        "lanes": ["Dirigeant", "Chargé d'affaires"],
        "nodes": [
            ("s", "start", "Début de semaine", 1, 0),
            ("t1", "task", "Consulter BOAMP et plateformes une à une", 1, 1),
            ("t2", "task", "Lire chaque avis en entier", 1, 2),
            ("t3", "task", "Chercher l'historique de l'acheteur (s'il y pense)", 1, 3),
            ("g1", "gateway", "Répondre ?", 0, 4),
            ("t4", "task", "Décider à l'intuition", 0, 5),
            ("t5", "task", "Monter le dossier de réponse", 1, 6),
            ("e1", "end", "Avis écarté", 0, 6),
            ("e2", "end", "Offre déposée", 1, 7),
        ],
        "flows": [
            ("s", "t1"),
            ("t1", "t2"),
            ("t2", "t3"),
            ("t3", "g1"),
            ("g1", "t4", "à voir"),
            ("g1", "e1", "non"),
            ("t4", "t5", "oui"),
            ("t5", "e2"),
        ],
        "notes": [
            "Irritants : 3 à 6 h/semaine de lecture (hypothèse), critères implicites,",
            "aucune visibilité sur la concurrence ni sur le titulaire sortant.",
        ],
    },
    "to-be": {
        "titre": "TO-BE — Veille outillée par Radar Marchés Publics",
        "lanes": ["Dirigeant", "Chargé d'affaires", "Radar (système)"],
        "nodes": [
            ("s", "start", "Profil défini une fois", 1, 0),
            ("a1", "auto", "Collecter les avis ouverts (BOAMP)", 2, 1),
            ("a2", "auto", "Classer : score hybride expliqué", 2, 2),
            ("a3", "auto", "Qualifier : grille go/no-go + historique DECP", 2, 3),
            ("t1", "task", "Revoir les 30 premiers avis", 1, 4),
            ("g1", "gateway", "Go ?", 0, 5),
            ("t2", "task", "Monter le dossier (lot ciblé)", 1, 6),
            ("e1", "end", "Écarté, motif tracé", 0, 6),
            ("e2", "end", "Offre déposée", 1, 7),
        ],
        "flows": [
            ("s", "a1"),
            ("a1", "a2"),
            ("a2", "a3"),
            ("a3", "t1"),
            ("t1", "g1"),
            ("g1", "t2", "go"),
            ("g1", "e1", "no-go"),
            ("t2", "e2"),
        ],
        "notes": [
            "Gains attendus (hypothèses à mesurer) : temps de veille ÷ 3,",
            "décision argumentée (concurrence, sortant, critères), taux de réponse en hausse.",
        ],
    },
}


def geom(node, n_lanes):
    _, typ, _, lane, col = node
    cx = X0 + col * STEP + W / 2
    cy = 40 + lane * LANE_H + LANE_H / 2
    if typ in ("start", "end"):
        return cx - 18, cy - 18, 36, 36
    if typ == "gateway":
        return cx - 25, cy - 25, 50, 50
    return cx - W / 2, cy - H / 2, W, H


def center(b):
    x, y, w, h = b
    return x + w / 2, y + h / 2


def anchors(b1, b2):
    (x1, y1), (x2, y2) = center(b1), center(b2)
    if abs(y1 - y2) < 1:
        return [(b1[0] + b1[2], y1), (b2[0], y2)]
    return (
        [(x1, y1 + (b1[3] / 2 if y2 > y1 else -b1[3] / 2)), (x1, y2), (b2[0], y2)]
        if x2 > x1
        else [(x1, y1), (x2, y1), (x2, y2)]
    )


def write(name, p):
    lanes, nodes = p["lanes"], p["nodes"]
    width = X0 + 8 * STEP + 40
    height = 40 + LANE_H * len(lanes) + 70
    boxes = {n[0]: geom(n, len(lanes)) for n in nodes}
    kind = {
        "start": "startEvent",
        "end": "endEvent",
        "task": "userTask",
        "auto": "serviceTask",
        "gateway": "exclusiveGateway",
    }
    # --- BPMN XML ---
    x = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
        'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="defs_'
        + name
        + '" targetNamespace="https://github.com/youssefmir/radar-marches-publics">',
        f'  <bpmn:collaboration id="collab"><bpmn:participant id="pool" name="{escape(p["titre"])}" processRef="proc"/></bpmn:collaboration>',
        '  <bpmn:process id="proc" isExecutable="false">',
        '    <bpmn:laneSet id="lanes">',
    ]
    for i, lane in enumerate(lanes):
        refs = "".join(f"<bpmn:flowNodeRef>{n[0]}</bpmn:flowNodeRef>" for n in nodes if n[3] == i)
        x.append(f'      <bpmn:lane id="lane{i}" name="{escape(lane)}">{refs}</bpmn:lane>')
    x.append("    </bpmn:laneSet>")
    for n in nodes:
        x.append(f'    <bpmn:{kind[n[1]]} id="{n[0]}" name="{escape(n[2])}"/>')
    for i, f in enumerate(p["flows"]):
        nm = f' name="{escape(f[2])}"' if len(f) > 2 else ""
        x.append(f'    <bpmn:sequenceFlow id="f{i}" sourceRef="{f[0]}" targetRef="{f[1]}"{nm}/>')
    x.append("  </bpmn:process>")
    x.append('  <bpmndi:BPMNDiagram id="diag"><bpmndi:BPMNPlane id="plane" bpmnElement="collab">')
    x.append(
        f'    <bpmndi:BPMNShape id="pool_di" bpmnElement="pool" isHorizontal="true"><dc:Bounds x="60" y="40" width="{width - 80}" height="{LANE_H * len(lanes)}"/></bpmndi:BPMNShape>'
    )
    for i in range(len(lanes)):
        x.append(
            f'    <bpmndi:BPMNShape id="lane{i}_di" bpmnElement="lane{i}" isHorizontal="true"><dc:Bounds x="90" y="{40 + i * LANE_H}" width="{width - 110}" height="{LANE_H}"/></bpmndi:BPMNShape>'
        )
    for n in nodes:
        bx, by, bw, bh = boxes[n[0]]
        x.append(
            f'    <bpmndi:BPMNShape id="{n[0]}_di" bpmnElement="{n[0]}"><dc:Bounds x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="{bh:.0f}"/></bpmndi:BPMNShape>'
        )
    for i, f in enumerate(p["flows"]):
        pts = anchors(boxes[f[0]], boxes[f[1]])
        wps = "".join(f'<di:waypoint x="{a:.0f}" y="{b:.0f}"/>' for a, b in pts)
        x.append(f'    <bpmndi:BPMNEdge id="f{i}_di" bpmnElement="f{i}">{wps}</bpmndi:BPMNEdge>')
    x.append("  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>")
    x.append("</bpmn:definitions>")
    (HERE / f"{name}.bpmn").write_text("\n".join(x) + "\n", encoding="utf-8")

    # --- SVG ---
    ink, rule, beacon, paper = "#14213D", "#DADDE2", "#E8731A", "#FDFDFB"
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="Public Sans, Helvetica, Arial, sans-serif" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="{paper}"/>',
        '<defs><marker id="arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
        f'<path d="M0,0 L10,4 L0,8 z" fill="{ink}"/></marker></defs>',
        f'<text x="60" y="26" font-size="15" font-weight="700" fill="{ink}" font-family="Bitter, Georgia, serif">{escape(p["titre"])}</text>',
        f'<rect x="60" y="40" width="{width - 80}" height="{LANE_H * len(lanes)}" fill="none" stroke="{ink}"/>',
    ]
    for i, lane in enumerate(lanes):
        y = 40 + i * LANE_H
        s.append(f'<rect x="60" y="{y}" width="30" height="{LANE_H}" fill="{ink}"/>')
        s.append(
            f'<text transform="translate(80 {y + LANE_H / 2}) rotate(-90)" text-anchor="middle" fill="{paper}" font-weight="600">{escape(lane)}</text>'
        )
        if i:
            s.append(f'<line x1="60" y1="{y}" x2="{width - 20}" y2="{y}" stroke="{ink}"/>')
    for f in p["flows"]:
        pts = anchors(boxes[f[0]], boxes[f[1]])
        d = "M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in pts)
        s.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="1.3" marker-end="url(#arr)"/>')
        if len(f) > 2:
            lx, ly = pts[-2] if len(pts) > 2 else pts[0]
            s.append(f'<text x="{lx + 6:.0f}" y="{ly - 6:.0f}" fill="#5C6470" font-size="11">{escape(f[2])}</text>')
    for n in nodes:
        bx, by, bw, bh = boxes[n[0]]
        cx, cy = bx + bw / 2, by + bh / 2
        if n[1] in ("start", "end"):
            sw = 1.5 if n[1] == "start" else 4
            s.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="{paper}" stroke="{ink}" stroke-width="{sw}"/>')
            ty = by - 8 if n[1] == "start" else by + bh + 16  # le libellé ne croise jamais le flux sortant
            s.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" fill="{ink}" font-size="11">{escape(n[2])}</text>')
        elif n[1] == "gateway":
            s.append(
                f'<path d="M{cx},{by} L{bx + bw},{cy} L{cx},{by + bh} L{bx},{cy} Z" fill="{paper}" stroke="{ink}" stroke-width="1.5"/>'
            )
            s.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-weight="700" fill="{ink}">×</text>')
            s.append(
                f'<text x="{cx}" y="{by - 8}" text-anchor="middle" fill="{ink}" font-size="11">{escape(n[2])}</text>'
            )
        else:
            fill = "#FFF4EA" if n[1] == "auto" else paper
            stroke = beacon if n[1] == "auto" else ink
            s.append(
                f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            )
            words, lines, cur = n[2].split(), [], ""
            for w in words:
                if len(cur) + len(w) + 1 > 20:
                    lines.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            lines.append(cur)
            for k, line in enumerate(lines):
                s.append(
                    f'<text x="{cx}" y="{cy - 7 * (len(lines) - 1) + 14 * k + 4}" text-anchor="middle" fill="{ink}">{escape(line)}</text>'
                )
            if n[1] == "auto":
                s.append(f'<text x="{bx + 6}" y="{by + 13}" fill="{beacon}" font-size="10" font-weight="700">⚙</text>')
    for k, line in enumerate(p["notes"]):
        s.append(
            f'<text x="60" y="{40 + LANE_H * len(lanes) + 26 + 16 * k}" fill="#5C6470" font-size="12">{escape(line)}</text>'
        )
    s.append("</svg>")
    (HERE / f"{name}.svg").write_text("\n".join(s) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for name, p in PROCESSES.items():
        write(name, p)
        print(f"{name}.bpmn / {name}.svg")
