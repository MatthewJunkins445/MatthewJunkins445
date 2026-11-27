"""Build the 3D contribution graphs for the README's "This month | This year" tabs.

Writes four files to profile-3d-contrib/:
  profile-3d-month.svg   the current month, starts over on the 1st
  profile-3d-year.svg    Jan 1 - Dec 31, starts over on January 1
  tab-month.svg, tab-year.svg   the tab buttons

The README puts each graph in a <details name="commit-graph"> whose <summary>
is a tab button. Details that share a name act like tabs: opening one closes
the other. The buttons are wrapped in <picture> so GitHub doesn't turn them
into links to the image (a click would open the image instead of the tab).

Both graphs use the same isometric view and face the same way: weeks run
top-left to bottom-right, days of the week bottom-left. The month graph is
the same picture zoomed in on this month.

Run by the daily profile workflow:
    GITHUB_TOKEN=... USERNAME=... python3 .github/scripts/profile_3d.py
Local preview:
    ... profile_3d.py --save-json data.json --out-dir preview   fetch, save, render
    profile_3d.py --from-json data.json --today 2026-08-15 --out-dir preview
"""
import argparse
import datetime as dt
import json
import math
import os
import urllib.request

OUT_DIR = "profile-3d-contrib"
SETTINGS = ".github/profile-3d-settings.json"

W, H = 1280, 850
TAN = math.tan(math.radians(30))
SHRINK = 0.9  # gap between bars

# Year graph: same geometry as github-profile-3d-contrib, which drew it before.
YEAR_DX = W / 64
# Month graph: bigger cells, placed in the space left of the radar chart.
MONTH_DX = W / 22
MONTH_ORIGIN = (480, 350)  # top corner of the first week's Sunday

RADAR_C, RADAR_R = (980, 290), 166
RADAR_AXES = [
    ("Commit", "totalCommitContributions"),
    ("Issue", "totalIssueContributions"),
    ("PullReq", "totalPullRequestContributions"),
    ("Review", "totalPullRequestReviewContributions"),
    ("Repo", "totalRepositoryContributions"),
]
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

STATS = " ".join(field for _, field in RADAR_AXES)
CALENDAR = ("contributionCalendar { totalContributions "
            "weeks { contributionDays { date contributionCount contributionLevel } } }")
QUERY = """
query($login: String!, $yf: DateTime!, $yt: DateTime!, $mf: DateTime!, $mt: DateTime!) {
  user(login: $login) {
    year: contributionsCollection(from: $yf, to: $yt) { %s %s }
    month: contributionsCollection(from: $mf, to: $mt) { %s %s }
  }
}""" % (STATS, CALENDAR, STATS, CALENDAR)
REPOS = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER) {
      pageInfo { hasNextPage endCursor } nodes { stargazerCount forkCount }
    }
  }
}"""


# ---------------------------------------------------------------- data

def graphql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"GraphQL error: {body['errors'][0]['message']}")
    return body["data"]["user"]


def month_range(today):
    first = today.replace(day=1)
    nxt = (first + dt.timedelta(days=32)).replace(day=1)
    return first, nxt - dt.timedelta(days=1)


def fetch(user, token, today):
    m_first, m_last = month_range(today)
    data = graphql(QUERY, {
        "login": user,
        "yf": f"{today.year}-01-01T00:00:00Z", "yt": f"{today.year}-12-31T23:59:59Z",
        "mf": f"{m_first}T00:00:00Z", "mt": f"{m_last}T23:59:59Z",
    }, token)
    stars = forks = 0
    after = None
    while True:
        repos = graphql(REPOS, {"login": user, "after": after}, token)["repositories"]
        stars += sum(n["stargazerCount"] for n in repos["nodes"])
        forks += sum(n["forkCount"] for n in repos["nodes"])
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    data.update(stars=stars, forks=forks)
    return data


def calendar_days(collection):
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"], LEVELS[d["contributionLevel"]])
            for w in collection["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return sorted(days)


# ---------------------------------------------------------------- colors

def rgb(hex_color, k=1.0):
    h = hex_color.lstrip("#")
    return "rgb(%d, %d, %d)" % tuple(round(int(h[i:i + 2], 16) * k) for i in (0, 2, 4))


def palette_css(s):
    out = [
        f".fg {{ fill: {s['foregroundColor']}; }}",
        f".bg {{ fill: {s['backgroundColor']}; }}",
        f".strong {{ fill: {s['strongColor']}; }}",
        f".weak {{ fill: {s['weakColor']}; }}",
        f".ring {{ fill: none; stroke: {s['weakColor']}; }}",
        f".icon {{ fill: none; stroke: {s['foregroundColor']}; }}",
        f".pill {{ fill: {s['strongColor']}; fill-opacity: 0.1; stroke: {s['strongColor']}; stroke-width: 2px; }}",
        f".radar {{ fill: {s['radarColor']}; fill-opacity: 0.5; stroke: {s['radarColor']}; stroke-width: 4px; }}",
    ]
    for i, c in enumerate(s["contribColors"]):
        # Same shading as github-profile-3d-contrib: lit top, darker sides.
        out.append(f".t{i} {{ fill: {rgb(c)}; }} .l{i} {{ fill: {rgb(c, 0.84)}; }} .r{i} {{ fill: {rgb(c, 0.7)}; }}")
    return "\n".join(out)


def svg_doc(width, height, title, body, settings):
    dark = dict(settings, **settings.get("darkMode", {}))
    css = "\n".join(['* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }',
                     palette_css(settings),
                     "@media (prefers-color-scheme: dark) {", palette_css(dark), "}"])
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
        f'<title id="title">{title}</title>',
        f"<style>\n{css}\n</style>",
        body,
        "</svg>",
    ])


# ---------------------------------------------------------------- graph parts

def pts(poly):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)


def bar(x, y, dx, count, level):
    """One day: a bar whose footprint's top corner is (x, y)."""
    h = math.log10(count / 20 + 1) * 144 + 3  # github-profile-3d-contrib's height curve
    a, b = dx * SHRINK, dx * TAN * SHRINK
    top = [(x, y - h), (x + a, y + b - h), (x, y + 2 * b - h), (x - a, y + b - h)]
    left = [(x - a, y + b - h), (x, y + 2 * b - h), (x, y + 2 * b), (x - a, y + b)]
    right = [(x, y + 2 * b - h), (x + a, y + b - h), (x + a, y + b), (x, y + 2 * b)]
    return (f'<polygon class="t{level}" points="{pts(top)}"/>'
            f'<polygon class="l{level}" points="{pts(left)}"/>'
            f'<polygon class="r{level}" points="{pts(right)}"/>')


def calendar_svg(days, dx, origin):
    """Isometric calendar: week w, weekday r (Sunday = 0) at origin + (w - r, w + r) cells."""
    first = days[0][0]
    sunday0 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    dy = dx * TAN
    out = []
    for d, count, level in days:  # date order is back-to-front
        r = (d.weekday() + 1) % 7
        w = (d - sunday0).days // 7
        out.append(bar(origin[0] + (w - r) * dx, origin[1] + (w + r) * dy, dx, count, level))
    return "".join(out)


def radar_point(i, frac):
    ang = math.radians(-90 + 72 * i)
    return (RADAR_C[0] + RADAR_R * frac * math.cos(ang),
            RADAR_C[1] + RADAR_R * frac * math.sin(ang))


def radar_svg(stats):
    def frac(v):  # log scale with rings at 1, 10, 100, 1K, 10K
        return 0 if v <= 0 else min(1, (math.log10(v) + 1) / 5)
    out = []
    for ring in range(1, 6):
        out.append(f'<polygon class="ring" stroke-dasharray="4 4" '
                   f'points="{pts(radar_point(i, ring / 5) for i in range(5))}"/>')
    for i in range(5):
        x, y = radar_point(i, 1)
        out.append(f'<line class="ring" stroke-dasharray="4 4" x1="{RADAR_C[0]}" '
                   f'y1="{RADAR_C[1]}" x2="{x:.1f}" y2="{y:.1f}"/>')
    for ring, label in enumerate(["1", "10", "100", "1K", "10K"], 1):
        x, y = radar_point(0, ring / 5)
        out.append(f'<text class="strong" x="{x + 3:.1f}" y="{y + 4:.1f}" font-size="11">{label}</text>')
    for i, (label, _) in enumerate(RADAR_AXES):
        x, y = radar_point(i, 1.13)
        anchor = "middle" if i == 0 else ("start" if i in (1, 2) else "end")
        if i in (2, 3):
            y += 12
        out.append(f'<text class="fg" x="{x:.1f}" y="{y:.1f}" font-size="17" text-anchor="{anchor}">{label}</text>')
    shape = pts(radar_point(i, frac(stats[f])) for i, (_, f) in enumerate(RADAR_AXES))
    out.append(f'<polygon class="radar" stroke-linejoin="round" points="{shape}"/>')
    return "".join(out)


def footer_svg(total, stars, forks):
    y = H - 20
    sx, fx = W * 5 / 10, W * 6 / 10
    star = []
    for k in range(10):
        rr = 12 if k % 2 == 0 else 5.4
        ang = math.radians(-90 + 36 * k)
        star.append((sx - 22 + rr * math.cos(ang), y - 10 + rr * math.sin(ang)))
    cx, cy = fx - 22, y - 10
    return (f'<text x="{W * 3 / 10}" y="{y}" text-anchor="end" class="strong" font-size="32" '
            f'font-weight="bold">{total}</text>'
            f'<text x="{W * 3 / 10 + 10}" y="{y}" class="fg" font-size="20">contributions</text>'
            f'<polygon class="fg" points="{pts(star)}"/>'
            f'<text x="{sx}" y="{y}" class="fg" font-size="28" font-weight="bold">{stars}</text>'
            f'<g class="icon" stroke-width="2.4">'
            f'<circle cx="{cx - 6}" cy="{cy - 9}" r="3"/><circle cx="{cx + 6}" cy="{cy - 9}" r="3"/>'
            f'<circle cx="{cx}" cy="{cy + 9}" r="3"/>'
            f'<path d="M{cx - 6} {cy - 6} v3 q0 3 3 3 h6 q3 0 3 -3 v-3 M{cx} {cy} v6"/></g>'
            f'<text x="{fx}" y="{y}" class="fg" font-size="28" font-weight="bold">{forks}</text>')


# ---------------------------------------------------------------- files

def graph_svg(collection, label, dx, origin, stars, forks, settings):
    days = calendar_days(collection)
    total = collection["contributionCalendar"]["totalContributions"]
    body = "".join([
        f'<rect class="bg" width="{W}" height="{H}"/>',
        f'<text x="40" y="56" class="fg" font-size="26" font-weight="bold">{label}</text>',
        calendar_svg(days, dx, origin),
        radar_svg(collection),
        footer_svg(total, stars, forks),
    ])
    return svg_doc(W, H, f"3D graph of my GitHub contributions, {label}: {total}", body, settings)


def tab_svg(label, settings):
    w, h = 200, 48
    body = (f'<rect class="pill" x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{h / 2 - 1}"/>'
            f'<text x="{w / 2}" y="{h / 2 + 7}" class="strong" font-size="20" font-weight="bold" '
            f'text-anchor="middle">{label}</text>')
    return svg_doc(w, h, label, body, settings)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-json", help="render saved data instead of fetching")
    ap.add_argument("--save-json", help="also save the fetched data here")
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD (UTC)")
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()

    today = (dt.date.fromisoformat(args.today) if args.today
             else dt.datetime.now(dt.timezone.utc).date())
    if args.from_json:
        data = json.load(open(args.from_json))
    else:
        data = fetch(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"], today)
        if args.save_json:
            json.dump(data, open(args.save_json, "w"))
    settings = json.load(open(SETTINGS))

    m_first, m_last = month_range(today)
    year_dy = YEAR_DX * TAN
    year_weeks = (len(calendar_days(data["year"])) + (dt.date(today.year, 1, 1).weekday() + 1) % 7 + 6) // 7
    files = {
        "profile-3d-month.svg": graph_svg(
            data["month"], f"{m_first:%b} {m_first.day} – {m_last:%b} {m_last.day}, {today.year}",
            MONTH_DX, MONTH_ORIGIN, data["stars"], data["forks"], settings),
        "profile-3d-year.svg": graph_svg(
            data["year"], f"Jan 1 – Dec 31, {today.year}",
            YEAR_DX, (YEAR_DX * 7, H - (year_weeks + 7) * year_dy), data["stars"], data["forks"], settings),
        "tab-month.svg": tab_svg("This month", settings),
        "tab-year.svg": tab_svg("This year", settings),
    }
    os.makedirs(args.out_dir, exist_ok=True)
    for name, svg in files.items():
        with open(os.path.join(args.out_dir, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print(f"wrote {', '.join(files)} to {args.out_dir} for {today:%B %Y}: "
          f"{data['month']['contributionCalendar']['totalContributions']} this month, "
          f"{data['year']['contributionCalendar']['totalContributions']} this year")


if __name__ == "__main__":
    main()
