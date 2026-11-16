"""Gera as ilustrações SVG dos cupcakes usados nos dados de demonstração."""
import os
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "app", "static", "img", "products")

# nome: (fundo, forminha, forminha listra, cobertura, cobertura sombra, topo)
PALETTE = {
    "chocolate": ("#f3e9e2", "#5b3a29", "#4a2e20", "#6b3f2a", "#54301f", "sprinkles-gold"),
    "brigadeiro": ("#efe4dc", "#3e2a20", "#2f1f17", "#4b2c1d", "#3a2115", "granulado"),
    "baunilha": ("#fbf5e6", "#e7c98f", "#d8b574", "#fff7e3", "#f1e2bf", "sprinkles"),
    "morango": ("#fdeef1", "#f0b9c4", "#e4a1b0", "#ffd5df", "#f7b8c8", "strawberry"),
    "redvelvet": ("#fbecec", "#9e1b2f", "#851426", "#fffaf3", "#efe4d6", "crumbs"),
    "limao": ("#f6f9e8", "#d9e59a", "#c6d47e", "#fffbe0", "#f2eab6", "lemon"),
    "docedeleite": ("#f8efe3", "#c8945a", "#b07d45", "#d9a066", "#c0884f", "drizzle"),
    "frutasvermelhas": ("#f8eef6", "#f3d6e3", "#e8bfd2", "#f6b3cc", "#e993b4", "berries"),
    "unicornio": ("#eef5fb", "#c8b6f2", "#b39ee9", "#7fdcd9", "#b89cf0", "star"),
    "cafe": ("#f1ebe6", "#8a6a55", "#755845", "#c8a68b", "#ad8b70", "bean"),
}


def topping(kind):
    if kind == "strawberry":
        return ('<path d="M200 70 C175 70 168 100 200 128 C232 100 225 70 200 70Z" fill="#e8394d"/>'
                '<path d="M188 70 l12 -12 l12 12 z" fill="#3c9a4a"/>'
                + "".join(f'<circle cx="{x}" cy="{y}" r="2" fill="#ffe08a"/>' for x, y in
                          [(192, 88), (206, 92), (198, 104), (210, 80), (188, 100)]))
    if kind == "lemon":
        return ('<circle cx="200" cy="92" r="24" fill="#f7d64a"/><circle cx="200" cy="92" r="18" fill="#fff3a6"/>'
                + "".join(f'<line x1="200" y1="92" x2="{200 + 18 * c}" y2="{92 + 18 * s}" stroke="#f7d64a" stroke-width="2"/>'
                          for c, s in [(1, 0), (-1, 0), (0, 1), (0, -1), (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7)]))
    if kind == "berries":
        return "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="{c}"/>' for x, y, c in
                       [(186, 100, "#3b4fa8"), (212, 98, "#c2185b"), (199, 82, "#e53950")])
    if kind == "star":
        return '<polygon points="200,62 209,88 236,88 214,104 222,130 200,114 178,130 186,104 164,88 191,88" fill="#ffd166"/>'
    if kind == "bean":
        return ('<ellipse cx="200" cy="96" rx="14" ry="20" fill="#4a2e20" transform="rotate(25 200 96)"/>'
                '<path d="M193 80 q12 16 0 32" stroke="#2d1b12" stroke-width="3" fill="none" transform="rotate(25 200 96)"/>')
    if kind == "drizzle":
        return ('<circle cx="200" cy="96" r="15" fill="#c0392b"/>'
                '<path d="M200 82 q6 -14 16 -18" stroke="#3c9a4a" stroke-width="3" fill="none"/>')
    if kind == "crumbs":
        return "".join(f'<rect x="{x}" y="{y}" width="9" height="9" rx="2" fill="#9e1b2f" transform="rotate({r} {x} {y})"/>'
                       for x, y, r in [(190, 92, 20), (206, 100, -15), (198, 80, 40), (214, 86, 10), (182, 104, -30)])
    colors = ["#e63946", "#f4a261", "#2a9d8f", "#8e7dbe", "#ffd166", "#4cc9f0"]
    if kind == "sprinkles-gold":
        colors = ["#e9c46a", "#f1d699", "#d4a017"]
    if kind == "granulado":
        colors = ["#2b1a12", "#3b2418"]
    pts = [(170, 140), (230, 132), (196, 118), (214, 156), (180, 160), (240, 160), (160, 168), (206, 138),
           (186, 132), (222, 116), (200, 100), (176, 150), (232, 176), (165, 182)]
    s = "".join(f'<rect x="{x}" y="{y}" width="12" height="4" rx="2" fill="{colors[i % len(colors)]}" '
                f'transform="rotate({(i * 47) % 180} {x} {y})"/>' for i, (x, y) in enumerate(pts))
    return s + '<circle cx="200" cy="84" r="14" fill="#d62839"/><path d="M200 70 q4 -14 14 -18" stroke="#5a3d2b" stroke-width="3" fill="none"/>'


def svg(bg, wrap, stripe, frost, shade, top):
    stripes = "".join(f'<path d="M{110 + i * 22} 240 L{124 + i * 18} 340" stroke="{stripe}" stroke-width="7"/>'
                      for i in range(9))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
<rect width="400" height="400" fill="{bg}"/>
<circle cx="70" cy="70" r="40" fill="#ffffff" opacity=".45"/><circle cx="340" cy="320" r="60" fill="#ffffff" opacity=".35"/>
<ellipse cx="200" cy="352" rx="110" ry="14" fill="#000" opacity=".08"/>
<clipPath id="w"><path d="M100 236 L300 236 L276 346 L124 346 Z"/></clipPath>
<path d="M100 236 L300 236 L276 346 L124 346 Z" fill="{wrap}"/>
<g clip-path="url(#w)">{stripes}</g>
<ellipse cx="200" cy="232" rx="118" ry="30" fill="{shade}"/>
<ellipse cx="200" cy="222" rx="112" ry="32" fill="{frost}"/>
<ellipse cx="200" cy="190" rx="92" ry="30" fill="{shade}"/>
<ellipse cx="200" cy="180" rx="88" ry="30" fill="{frost}"/>
<ellipse cx="200" cy="150" rx="66" ry="26" fill="{shade}"/>
<ellipse cx="200" cy="142" rx="62" ry="26" fill="{frost}"/>
<ellipse cx="200" cy="114" rx="38" ry="20" fill="{frost}"/>
<ellipse cx="172" cy="170" rx="20" ry="7" fill="#fff" opacity=".35"/>
{topping(top)}
</svg>'''


def main(out=OUT):
    os.makedirs(out, exist_ok=True)
    for name, p in PALETTE.items():
        with open(os.path.join(out, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg(*p))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
