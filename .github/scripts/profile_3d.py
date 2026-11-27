"""Build the animated 3D contribution graph: this month <-> this year.

One SVG with "This month | This year" tabs drawn at the top. It shows the
current month, then every day's bar slides and shrinks into its place in the
whole-year graph, holds, slides back, and loops. GitHub READMEs can't run
scripts or take clicks, so the tabs switch on their own (SMIL animation, which
works in <img> SVGs).

Both views are drawn with the same isometric angle and run the same way
(top-left to bottom-right): the year view lays weeks along that axis like
github-profile-3d-contrib did, and the month view lays each week out as a row
of days along it, like a calendar seen from its top-left corner.

Ranges are worked out on every run, so the month view starts over on the 1st
and the year view on January 1.

Run by the daily profile workflow:
    GITHUB_TOKEN=... USERNAME=... python3 .github/scripts/profile_3d.py
Local preview:
    ... profile_3d.py --save-json data.json     fetch, save the data, render
    profile_3d.py --from-json data.json [--today 2026-08-15]   render saved data
"""
import argparse
import datetime as dt
import json
import math
import os
import urllib.request

OUT = "profile-3d-contrib/profile-3d.svg"
SETTINGS = ".github/profile-3d-settings.json"

W, H = 1280, 850
TAN = math.tan(math.radians(30))

# Year view: same geometry as github-profile-3d-contrib, so it looks unchanged.
YEAR_DX = W / 64
# Month view: bigger cells, placed in the space left of the radar chart.
MONTH_DX = 58
MONTH_ORIGIN = (380, 300)  # top corner of the first week's Sunday
SHRINK = 0.9  # gap between bars

# Animation: month hold, morph, year hold, morph back (seconds).
HOLD_MONTH, MORPH, HOLD_YEAR = 5.0, 1.5, 6.0
DUR = HOLD_MONTH + MORPH + HOLD_YEAR + MORPH
_t = [0, HOLD_MONTH, HOLD_MONTH + MORPH, HOLD_MONTH + MORPH + HOLD_YEAR, DUR]
KEY_TIMES = ";".join(f"{t / DUR:.4f}" for t in _t)
EASE = "0.45 0 0.25 1"
KEY_SPLINES = f"0 0 1 1;{EASE};0 0 1 1;{EASE}"

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
QUERY = """
query($login: String!, $yf: DateTime!, $yt: DateTime!, $mf: DateTime!, $mt: DateTime!) {
  user(login: $login) {
    year: contributionsCollection(from: $yf, to: $yt) {
      %s
      contributionCalendar { totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } } }
    }
    month: contributionsCollection(from: $mf, to: $mt) {
      %s
      contributionCalendar { totalContributions }
    }
  }
}""" % (STATS, STATS)
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
    user_data = graphql(QUERY, {
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
    return {"year": user_data["year"], "month": user_data["month"],
            "stars": stars, "forks": forks}


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
        f".track {{ fill: {s['weakColor']}; fill-opacity: 0.12; }}",
        f".radar {{ fill: {s['radarColor']}; fill-opacity: 0.5; stroke: {s['radarColor']}; stroke-width: 4px; }}",
    ]
    for i, c in enumerate(s["contribColors"]):
        # Same shading as github-profile-3d-contrib: lit top, darker sides.
        out.append(f".t{i} {{ fill: {rgb(c)}; }} .l{i} {{ fill: {rgb(c, 0.84)}; }} .r{i} {{ fill: {rgb(c, 0.7)}; }}")
    return "\n".join(out)


# ---------------------------------------------------------------- geometry

def bar_height(count):
    """github-profile-3d-contrib's height curve (log, so busy days don't dwarf the rest)."""
    return math.log10(count / 20 + 1) * 144 + 3


def faces(x, y, dx, h):
    """Top, left and right faces of a bar whose footprint's top corner is (x, y)."""
    a, b = dx * SHRINK, dx * TAN * SHRINK
    top = [(x, y - h), (x + a, y + b - h), (x, y + 2 * b - h), (x - a, y + b - h)]
    left = [(x - a, y + b - h), (x, y + 2 * b - h), (x, y + 2 * b), (x - a, y + b)]
    right = [(x, y + 2 * b - h), (x + a, y + b - h), (x + a, y + b), (x, y + 2 * b)]
    return top, left, right


def pts(poly):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)


def animate(attr, month_value, year_value):
    values = ";".join([month_value, month_value, year_value, year_value, month_value])
    return (f'<animate attributeName="{attr}" values="{values}" dur="{DUR:g}s" '
            f'keyTimes="{KEY_TIMES}" calcMode="spline" keySplines="{KEY_SPLINES}" '
            f'repeatCount="indefinite"/>')


def bar_svg(level, month_xy, year_xy, h):
    """A bar that sits at month_xy in the month view and morphs to year_xy."""
    out = []
    m_faces = faces(*month_xy, MONTH_DX, h)
    y_faces = faces(*year_xy, YEAR_DX, h)
    for cls, mf, yf in zip("tlr", m_faces, y_faces):
        out.append(f'<polygon class="{cls}{level}" points="{pts(mf)}">'
                   f'{animate("points", pts(mf), pts(yf))}</polygon>')
    return "".join(out)


def static_bar_svg(level, year_xy, h):
    top, left, right = faces(*year_xy, YEAR_DX, h)
    return (f'<polygon class="t{level}" points="{pts(top)}"/>'
            f'<polygon class="l{level}" points="{pts(left)}"/>'
            f'<polygon class="r{level}" points="{pts(right)}"/>')


# ---------------------------------------------------------------- parts

def calendar_svg(days, today):
    """days: [(date, count, level)] for the whole year, in date order."""
    first = days[0][0]
    sunday0 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    weeks = (len(days) + (first.weekday() + 1) % 7 + 6) // 7
    dy = YEAR_DX * TAN
    off_x, off_y = YEAR_DX * 7, H - (weeks + 7) * dy

    m_first, _ = month_range(today)
    m_first_dow = (m_first.weekday() + 1) % 7
    mdy = MONTH_DX * TAN

    # Painter's order is date order in both views, so split the year into
    # before / this month / after and fade the other two in for the year view.
    before, month, after = [], [], []
    for d, count, level in days:
        dow = (d.weekday() + 1) % 7  # Sunday = 0
        week = (d - sunday0).days // 7
        year_xy = (off_x + (week - dow) * YEAR_DX, off_y + (week + dow) * dy)
        h = bar_height(count)
        if (d.year, d.month) == (today.year, today.month):
            row = (d.day - 1 + m_first_dow) // 7  # week of the month
            month_xy = (MONTH_ORIGIN[0] + (dow - row) * MONTH_DX,
                        MONTH_ORIGIN[1] + (dow + row) * mdy)
            month.append(bar_svg(level, month_xy, year_xy, h))
        else:
            (before if d < m_first else after).append(static_bar_svg(level, year_xy, h))

    fade = animate("opacity", "0", "1")
    return (f'<g opacity="0">{fade}{"".join(before)}</g>'
            f'{"".join(month)}'
            f'<g opacity="0">{fade}{"".join(after)}</g>')


def radar_point(i, frac):
    ang = math.radians(-90 + 72 * i)
    return (RADAR_C[0] + RADAR_R * frac * math.cos(ang),
            RADAR_C[1] + RADAR_R * frac * math.sin(ang))


def radar_frac(v):
    """Log scale with rings at 1, 10, 100, 1K, 10K."""
    return 0 if v <= 0 else min(1, (math.log10(v) + 1) / 5)


def radar_svg(month, year):
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
    m = pts(radar_point(i, radar_frac(month[f])) for i, (_, f) in enumerate(RADAR_AXES))
    y_ = pts(radar_point(i, radar_frac(year[f])) for i, (_, f) in enumerate(RADAR_AXES))
    out.append(f'<polygon class="radar" stroke-linejoin="round" points="{m}">{animate("points", m, y_)}</polygon>')
    return "".join(out)


def crossfade(month_svg, year_svg):
    return (f'<g opacity="1">{animate("opacity", "1", "0")}{month_svg}</g>'
            f'<g opacity="0">{animate("opacity", "0", "1")}{year_svg}</g>')


def tabs_svg(today):
    x0, y0, tw, th = 40, 28, 190, 52
    m_first, m_last = month_range(today)
    out = [f'<rect class="track" x="{x0 - 4}" y="{y0 - 4}" width="{2 * tw + 8}" height="{th + 8}" rx="{th / 2 + 4}"/>',
           f'<rect class="strong" x="{x0}" y="{y0}" width="{tw}" height="{th}" rx="{th / 2}">'
           f'{animate("x", str(x0), str(x0 + tw))}</rect>']
    for i, label in enumerate(["This month", "This year"]):
        cx, cy = x0 + tw * i + tw / 2, y0 + th / 2 + 8
        text = f'x="{cx}" y="{cy}" font-size="22" font-weight="bold" text-anchor="middle">{label}</text>'
        on, off = ("1", "0") if i == 0 else ("0", "1")
        out.append(f'<text class="weak" {text}')
        out.append(f'<g opacity="{on}">{animate("opacity", on, off)}<text class="bg" {text}</g>')
    month_label = f"{m_first:%b} {m_first.day} – {m_last:%b} {m_last.day}, {today.year}"
    year_label = f"Jan 1 – Dec 31, {today.year}"
    sub = 'x="{}" y="{}" font-size="19" class="weak">{}</text>'
    out.append(crossfade(f'<text {sub.format(x0 + 8, y0 + th + 36, month_label)}',
                         f'<text {sub.format(x0 + 8, y0 + th + 36, year_label)}'))
    return "".join(out)


def star_path(cx, cy, r):
    p = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        ang = math.radians(-90 + 36 * k)
        p.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return f'<polygon class="fg" points="{pts(p)}"/>'


def fork_icon(cx, cy):
    return (f'<g class="icon" stroke-width="2.4">'
            f'<circle cx="{cx - 6}" cy="{cy - 9}" r="3"/><circle cx="{cx + 6}" cy="{cy - 9}" r="3"/>'
            f'<circle cx="{cx}" cy="{cy + 9}" r="3"/>'
            f'<path d="M{cx - 6} {cy - 6} v3 q0 3 3 3 h6 q3 0 3 -3 v-3 M{cx} {cy} v6"/></g>')


def footer_svg(month_total, year_total, stars, forks):
    y = H - 20
    def contrib(n):
        return (f'<text x="{W * 3 / 10}" y="{y}" text-anchor="end" class="strong" font-size="32" '
                f'font-weight="bold">{n}</text>'
                f'<text x="{W * 3 / 10 + 10}" y="{y}" class="fg" font-size="20">contributions</text>')
    sx, fx = W * 5 / 10, W * 6 / 10
    return (crossfade(contrib(month_total), contrib(year_total))
            + star_path(sx - 22, y - 10, 12)
            + f'<text x="{sx}" y="{y}" class="fg" font-size="28" font-weight="bold">{stars}</text>'
            + fork_icon(fx - 22, y - 10)
            + f'<text x="{fx}" y="{y}" class="fg" font-size="28" font-weight="bold">{forks}</text>')


# ---------------------------------------------------------------- page

def render(data, settings, today):
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"], LEVELS[d["contributionLevel"]])
            for w in data["year"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort()
    month_total = data["month"]["contributionCalendar"]["totalContributions"]
    year_total = data["year"]["contributionCalendar"]["totalContributions"]
    dark = dict(settings, **settings.get("darkMode", {}))
    css = "\n".join([
        '* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }',
        palette_css(settings),
        "@media (prefers-color-scheme: dark) {", palette_css(dark), "}",
    ])
    title = (f"3D graph of my GitHub contributions, switching between this month "
             f"({month_total}) and this year ({year_total})")
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="title">',
        f'<title id="title">{title}</title>',
        f"<style>\n{css}\n</style>",
        f'<rect class="bg" width="{W}" height="{H}"/>',
        calendar_svg(days, today),
        radar_svg(data["month"], data["year"]),
        tabs_svg(today),
        footer_svg(month_total, year_total, data["stars"], data["forks"]),
        "</svg>",
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-json", help="render saved data instead of fetching")
    ap.add_argument("--save-json", help="also save the fetched data here")
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD (UTC)")
    ap.add_argument("--out", default=OUT)
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

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(data, settings, today))
    print(f"wrote {args.out} for {today:%B %Y}: "
          f"{data['month']['contributionCalendar']['totalContributions']} this month, "
          f"{data['year']['contributionCalendar']['totalContributions']} this year")


if __name__ == "__main__":
    main()
