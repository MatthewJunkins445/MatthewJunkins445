"""Build a waffle chart of every language in the user's public repos.

100 squares, one per percent of code (bytes, as GitHub's linguist counts it),
in the same square-grid style as the ATT&CK matrix in the README.

Run by the daily profile workflow:
    GITHUB_TOKEN=... USERNAME=... python3 .github/scripts/languages.py
For a local preview from saved data:
    python3 .github/scripts/languages.py --from-json langs.json
"""
import json
import os
import sys
import urllib.request

OUT = "profile-3d-contrib/languages.svg"
GRAPH = "profile-3d-contrib/profile-3d.svg"

# GitHub linguist colors, so slices match the language pie in the 3D graph.
COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "CSS": "#663399", "HTML": "#e34c26", "Rust": "#dea584", "Shell": "#89e051",
    "PowerShell": "#012456", "Batchfile": "#C1F12E", "Java": "#b07219",
    "Go": "#00ADD8", "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "Ruby": "#701516",
    "PHP": "#4F5D95", "Kotlin": "#A97BFF", "Swift": "#F05138", "SCSS": "#c6538c",
    "Vue": "#41b883", "Makefile": "#427819", "HCL": "#844FBA", "Lua": "#000080",
    "Dart": "#00B4AB", "Svelte": "#ff3e00", "Astro": "#ff5a03", "Nix": "#7e7eff",
    "YARA": "#220000", "Sigma": "#3a3a3a",
}
FALLBACK = "#8b949e"

W = 793
COLS, ROWS = 50, 2
PITCH = W / COLS
CELL = 13
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


def api(path, token):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch(user, token):
    totals, page = {}, 1
    while True:
        repos = api(f"users/{user}/repos?type=owner&per_page=100&page={page}", token)
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["private"] or repo["name"].lower() == user.lower():
                continue
            for lang, n in api(f"repos/{user}/{repo['name']}/languages", token).items():
                totals[lang] = totals.get(lang, 0) + n
        page += 1
    return totals


def squares(totals):
    """Largest-remainder rounding so the squares always add up to 100."""
    total = sum(totals.values())
    exact = {k: v * 100 / total for k, v in totals.items()}
    counts = {k: int(x) for k, x in exact.items()}
    for k in sorted(exact, key=lambda k: exact[k] - counts[k], reverse=True)[: 100 - sum(counts.values())]:
        counts[k] += 1
    return exact, counts


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def render(totals):
    langs = sorted(totals, key=totals.get, reverse=True)
    exact, counts = squares(totals)
    p = []
    i = 0
    grid_y = 0
    for lang in langs:
        for _ in range(counts[lang]):
            col, row = i // ROWS, i % ROWS  # fill column by column, like a bar
            x = col * PITCH
            y = grid_y + row * (CELL + 3)
            p.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" fill="{COLORS.get(lang, FALLBACK)}"/>')
            i += 1

    # legend: flows left to right, wraps to new lines
    x, y = 0.0, grid_y + ROWS * (CELL + 3) + 30
    for lang in langs:
        pct = exact[lang]
        label = f"{lang} {pct:.1f}%" if pct >= 0.1 else f"{lang} <0.1%"
        w = 16 + len(label) * 7.6 + 22  # rough width at 14px
        if x + w > W and x > 0:
            x, y = 0.0, y + 26
        p.append(f'<rect x="{x:.1f}" y="{y - 10}" width="10" height="10" fill="{COLORS.get(lang, FALLBACK)}"/>')
        p.append(f'<text class="lg" x="{x + 16:.1f}" y="{y}"><tspan class="nm">{esc(lang)}</tspan> {label[len(lang) + 1:]}</text>')
        x += w
    h = y + 12

    alt = "Languages in my public repos by amount of code: " + ", ".join(
        f"{lang} {exact[lang]:.1f}%" for lang in langs)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h:.0f}" viewBox="0 0 {W} {h:.0f}" role="img" aria-labelledby="t">
<title id="t">{esc(alt)}</title>
<style>
text{{font-family:{FONT};}}
.lg{{font-size:14px;fill:#59636E;}}
.nm{{fill:#1F2328;font-weight:600;}}
@media (prefers-color-scheme:dark){{.lg{{fill:#9198A1;}}.nm{{fill:#E6EDF3;}}}}
</style>
{chr(10).join(p)}
</svg>
"""


def strip_pie(path):
    """Remove the 3D graph's language pie; this chart replaces it.

    github-profile-3d-contrib has no setting to hide the pie. It draws it as a
    top-level <g transform="translate(40, ...)">, so drop that group.
    """
    import re
    import xml.etree.ElementTree as ET
    if not os.path.exists(path):
        return
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(path)
    root = tree.getroot()
    pies = [g for g in root
            if g.tag.endswith("}g") and re.match(r"translate\(40,", g.get("transform", ""))]
    for g in pies:
        root.remove(g)
    if pies:
        tree.write(path, encoding="unicode")
    print(f"removed {len(pies)} pie group(s) from {path}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--from-json":
        totals = json.load(open(sys.argv[2]))
    else:
        totals = fetch(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"])
    strip_pie(GRAPH)
    if not totals:
        print("no languages found; leaving the existing chart in place")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(render(totals))
    print(f"wrote {OUT}: " + ", ".join(sorted(totals, key=totals.get, reverse=True)))


if __name__ == "__main__":
    main()
