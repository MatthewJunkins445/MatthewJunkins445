"""Build the 3D contribution graph: this year, with this month zoomed in.

One still SVG, profile-3d-contrib/profile-3d.svg:
  - this year (Jan 1 - Dec 31) runs across the middle, top-left to bottom-right
  - this month, zoomed in, sits in the bottom-left corner below it
  - the radar chart (commits, issues, PRs, reviews, repos) sits top-right,
    with this month and this year overlaid

Both calendars run top-left to bottom-right: the year lays its weeks along
that line like github-profile-3d-contrib drew it, and the month lays out each
week as a row of days along it (Sunday at the top-left end). Ranges are
worked out on every run, so the month starts over on the 1st and the year on
January 1.

Run by the daily profile workflow:
    GITHUB_TOKEN=... USERNAME=... python3 .github/scripts/profile_3d.py
Local preview:
    ... profile_3d.py --save-json data.json --out preview.svg   fetch, save, render
    profile_3d.py --from-json data.json --today 2026-08-15 --out preview.svg
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
SHRINK = 0.9  # gap between bars

# Year: same geometry as github-profile-3d-contrib, which drew it before.
YEAR_DX = W / 64
# Month: bigger cells, in the bottom-left corner below the year.
MONTH_DX = 38
MONTH_ORIGIN = (260, 545)  # top corner of the first week's Sunday
MONTH_TITLE = (30, 790)  # under the month's lower-left edge
YEAR_TITLE = (40, 50)
# Radar: top-right corner, above the year. Filled shape = this year,
# dashed outline = this month.
RADAR_C, RADAR_R = (1020, 265), 150

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


def total(collection):
    return collection["contributionCalendar"]["totalContributions"]


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
        f".radar-year {{ fill: {s['radarColor']}; fill-opacity: 0.45; stroke: {s['radarColor']}; stroke-width: 3px; }}",
        f".radar-month {{ fill: none; stroke: {s['foregroundColor']}; stroke-width: 2.5px; stroke-dasharray: 7 5; }}",
    ]
    for i, c in enumerate(s["contribColors"]):
        # Same shading as github-profile-3d-contrib: lit top, darker sides.
        out.append(f".t{i} {{ fill: {rgb(c)}; }} .l{i} {{ fill: {rgb(c, 0.84)}; }} .r{i} {{ fill: {rgb(c, 0.7)}; }}")
    return "\n".join(out)


# ---------------------------------------------------------------- parts

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


def calendar_svg(days, dx, origin, weeks_as_rows=False):
    """Isometric calendar, week w and weekday r (Sunday = 0).

    Default (year): weeks run top-left to bottom-right, at origin + (w - r, w + r) cells.
    weeks_as_rows (month): each week is a row of days running top-left to
    bottom-right, at origin + (r - w, r + w) cells, so the month's long side
    points the same way as the year's.
    """
    first = days[0][0]
    sunday0 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    dy = dx * TAN
    out = []
    for d, count, level in days:  # date order is back-to-front in both layouts
        r = (d.weekday() + 1) % 7
        w = (d - sunday0).days // 7
        along, across = (r, w) if weeks_as_rows else (w, r)
        out.append(bar(origin[0] + (along - across) * dx, origin[1] + (along + across) * dy,
                       dx, count, level))
    return "".join(out)


def title_svg(xy, heading, sub, anchor):
    x, y = xy
    return (f'<text x="{x}" y="{y}" class="fg" font-size="26" font-weight="bold" '
            f'text-anchor="{anchor}">{heading}</text>'
            f'<text x="{x}" y="{y + 26}" class="weak" font-size="18" text-anchor="{anchor}">{sub}</text>')


def radar_point(i, frac):
    ang = math.radians(-90 + 72 * i)
    return (RADAR_C[0] + RADAR_R * frac * math.cos(ang),
            RADAR_C[1] + RADAR_R * frac * math.sin(ang))


def radar_svg(month, year):
    def frac(v):  # log scale with rings at 1, 10, 100, 1K, 10K
        return 0 if v <= 0 else min(1, (math.log10(v) + 1) / 5)

    def shape(stats):
        return pts(radar_point(i, frac(stats[f])) for i, (_, f) in enumerate(RADAR_AXES))

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
        out.append(f'<text class="fg" x="{x:.1f}" y="{y:.1f}" font-size="16" text-anchor="{anchor}">{label}</text>')
    out.append(f'<polygon class="radar-year" stroke-linejoin="round" points="{shape(year)}"/>')
    out.append(f'<polygon class="radar-month" stroke-linejoin="round" points="{shape(month)}"/>')
    return "".join(out)


def footer_svg(month_total, year_total, stars, forks):
    y = H - 20
    x0 = 465  # right of the month, left of where the year's last weeks reach the bottom
    out = [f'<text x="{x0}" y="{y}" text-anchor="end" class="strong" font-size="32" '
           f'font-weight="bold">{month_total}</text>'
           f'<text x="{x0 + 10}" y="{y}" class="fg" font-size="20">this month</text>',
           f'<text x="{x0 + 230}" y="{y}" text-anchor="end" class="strong" font-size="32" '
           f'font-weight="bold">{year_total}</text>'
           f'<text x="{x0 + 240}" y="{y}" class="fg" font-size="20">this year</text>']
    sx, fx = x0 + 400, x0 + 500
    star = []
    for k in range(10):
        rr = 12 if k % 2 == 0 else 5.4
        ang = math.radians(-90 + 36 * k)
        star.append((sx - 22 + rr * math.cos(ang), y - 10 + rr * math.sin(ang)))
    cx, cy = fx - 22, y - 10
    out.append(f'<polygon class="fg" points="{pts(star)}"/>'
               f'<text x="{sx}" y="{y}" class="fg" font-size="28" font-weight="bold">{stars}</text>'
               f'<g class="icon" stroke-width="2.4">'
               f'<circle cx="{cx - 6}" cy="{cy - 9}" r="3"/><circle cx="{cx + 6}" cy="{cy - 9}" r="3"/>'
               f'<circle cx="{cx}" cy="{cy + 9}" r="3"/>'
               f'<path d="M{cx - 6} {cy - 6} v3 q0 3 3 3 h6 q3 0 3 -3 v-3 M{cx} {cy} v6"/></g>'
               f'<text x="{fx}" y="{y}" class="fg" font-size="28" font-weight="bold">{forks}</text>')
    return "".join(out)


# ---------------------------------------------------------------- page

def render(data, settings, today):
    m_first, m_last = month_range(today)
    year_days = calendar_days(data["year"])
    first = year_days[0][0]
    weeks = (len(year_days) + (first.weekday() + 1) % 7 + 6) // 7
    year_origin = (YEAR_DX * 7, H - (weeks + 7) * YEAR_DX * TAN)
    m_total, y_total = total(data["month"]), total(data["year"])

    dark = dict(settings, **settings.get("darkMode", {}))
    css = "\n".join(['* { font-family: "Ubuntu", "Helvetica", "Arial", sans-serif; }',
                     palette_css(settings),
                     "@media (prefers-color-scheme: dark) {", palette_css(dark), "}"])
    title = (f"3D graphs of my GitHub contributions: this year ({y_total}) and "
             f"this month ({m_total}), plus a radar chart of commits, issues, PRs, reviews and repos")
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="title">',
        f'<title id="title">{title}</title>',
        f"<style>\n{css}\n</style>",
        f'<rect class="bg" width="{W}" height="{H}"/>',
        title_svg(YEAR_TITLE, "This year", f"Jan 1 – Dec 31, {today.year}", "start"),
        title_svg(MONTH_TITLE, "This month",
                  f"{m_first:%b} {m_first.day} – {m_last:%b} {m_last.day}, {today.year}", "start"),
        calendar_svg(calendar_days(data["month"]), MONTH_DX, MONTH_ORIGIN, weeks_as_rows=True),
        calendar_svg(year_days, YEAR_DX, year_origin),
        radar_svg(data["month"], data["year"]),
        footer_svg(m_total, y_total, data["stars"], data["forks"]),
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

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(data, settings, today))
    print(f"wrote {args.out} for {today:%B %Y}: "
          f"{total(data['month'])} this month, {total(data['year'])} this year")


if __name__ == "__main__":
    main()
