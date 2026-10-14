"""Fetch own commits and render a compact technology timeline (Python stdlib only)."""

import argparse
from datetime import date, datetime, time, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
JST = timezone(timedelta(hours=9))


class TimelineError(Exception):
    pass


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def week_start(year):
    start = date(year, 1, 1)
    return start - timedelta(days=start.weekday())


def week_index(day, year):
    return (day - week_start(year)).days // 7


def rows(data):
    return [row for group in data["groups"] for row in group["rows"]]


def load_sources(path, private_json, valid_ids):
    try:
        public = read_json(path)
        private = json.loads(private_json) if private_json else []
        if not isinstance(public, list) or not isinstance(private, list):
            raise ValueError
        sources = public + private
        for source in sources:
            if not isinstance(source, dict) or set(source) - {"repo", "technologies", "path", "ref", "since", "until"}:
                raise ValueError
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source.get("repo", "")):
                raise ValueError
            ids = source.get("technologies")
            if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in valid_ids for i in ids):
                raise ValueError
            for key in ("path", "ref"):
                if key in source and (not isinstance(source[key], str) or not source[key]):
                    raise ValueError
            for key in ("since", "until"):
                if key in source:
                    date.fromisoformat(source[key])
            if source.get("since", "0001-01-01") > source.get("until", "9999-12-31"):
                raise ValueError
        return sources
    except (ValueError, TypeError, OSError):
        # Never echo configuration: it can contain private repository names.
        raise TimelineError("Invalid source configuration. Check sources.json / TIMELINE_SOURCES_JSON.") from None


class GitHub:
    def __init__(self, token):
        self.headers = {"Accept": "application/vnd.github+json", "User-Agent": "technology-timeline",
                        "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def request(self, url):
        try:
            with urlopen(Request(url, headers=self.headers), timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            raise TimelineError(f"GitHub API returned HTTP {error.code}. Check access, sources, and rate limits; no files updated.") from None
        except (URLError, TimeoutError, ValueError):
            raise TimelineError("GitHub API request failed; no files updated.") from None

    def commits(self, source, author, start, end):
        params = {"author": author, "per_page": 100,
                  "since": datetime.combine(start, time.min, JST).isoformat(),
                  "until": datetime.combine(end, time(23, 59, 59), JST).isoformat()}
        for key, api_key in (("path", "path"), ("ref", "sha")):
            if key in source:
                params[api_key] = source[key]
        page = 1
        while True:
            params["page"] = page
            batch = self.request(f"https://api.github.com/repos/{quote(source['repo'], safe='/')}/commits?{urlencode(params)}")
            if not isinstance(batch, list):
                raise TimelineError("Unexpected GitHub API response; no files updated.")
            yield from batch
            if len(batch) < 100:
                return
            page += 1


def aggregate(baseline, sources, as_of, github):
    result = json.loads(json.dumps(baseline))
    year = result["year"]
    snapshot = date.fromisoformat(result.pop("through"))
    as_of = min(as_of, date(year, 12, 31))
    if as_of < snapshot:
        raise TimelineError("The requested date precedes the saved baseline.")
    result["as_of"] = as_of.isoformat()
    by_id = {row["id"]: row for row in rows(result)}
    for row in by_id.values():
        row["through"] = snapshot.isoformat() if row["weeks"] is not None else None
    cache = {}
    for source in sources:
        start = max(date(year, 1, 1), date.fromisoformat(source.get("since", (snapshot + timedelta(days=1)).isoformat())))
        end = min(as_of, date.fromisoformat(source.get("until", as_of.isoformat())))
        if start > end:
            continue
        key = (source["repo"], source.get("path"), source.get("ref"), start, end)
        if key not in cache:
            weeks = set()
            for commit in github.commits(source, result["author"], start, end):
                author = commit.get("author") or {}
                if author.get("login", "").lower() != result["author"].lower() or author.get("type") == "Bot":
                    continue
                try:
                    stamp = datetime.fromisoformat(commit["commit"]["committer"]["date"].replace("Z", "+00:00"))
                    if stamp.tzinfo is None:
                        raise ValueError
                    day = stamp.astimezone(JST).date()
                except (KeyError, TypeError, ValueError):
                    raise TimelineError("A commit has an invalid timestamp; no files updated.") from None
                if start <= day <= end:
                    weeks.add(week_index(day, year))
            cache[key] = weeks
        for tech in source["technologies"]:
            row = by_id[tech]
            # A configured repository without any commits does not establish usage dates.
            if row["weeks"] is None and not cache[key]:
                continue
            row["weeks"] = sorted(set(row["weeks"] or []) | cache[key])
            row["through"] = max(row["through"] or end.isoformat(), end.isoformat())
    return result


def prevent_regression(previous, current):
    """Missing secrets or removed mappings must not silently erase published activity."""
    old_rows = {row["id"]: row for row in rows(previous)}
    for row in rows(current):
        old = old_rows.get(row["id"], {})
        if (old.get("through") or "") > (row["through"] or "") or not set(old.get("weeks") or []).issubset(row["weeks"] or []):
            raise TimelineError("Published history would be lost. Restore the source configuration or explicitly review the saved activity file; no files updated.")


def render_svg(data, dark=False):
    colors = ({"bg": "#0d1117", "fg": "#e5edf6", "muted": "#a8b5c7", "line": "#2b394b", "empty": "#202d40", "blue": "#79aef8"}
              if dark else {"bg": "#ffffff", "fg": "#202d3d", "muted": "#596879", "line": "#dee5ed", "empty": "#eaf0f6", "blue": "#387bd5"})
    year = data["year"]
    count = week_index(date(year, 12, 31), year) + 1
    width, x_track, step = 800, 302, 9
    height = 102 + len(rows(data)) * 22 + len(data["groups"]) * 16
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{year} 使った技術と活動時期</title>',
           '<desc id="desc">1マスは月曜始まりの1週。技術を使うリポジトリに本人のコミットがあった週を表示。点は集計対象外・未確認。履歴だけで期間を特定できない技術は時期未確認。</desc>',
           f'<rect width="{width}" height="{height}" rx="10" fill="{colors["bg"]}"/>',
           '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Noto Sans CJK JP, Noto Sans JP, Meiryo, sans-serif">']

    def text(x, y, label, size=12, color="fg", extra=""):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{colors[color]}" {extra}>{escape(str(label))}</text>')

    def line(x1, y, x2):
        svg.append(f'<path d="M{x1} {y}H{x2}" stroke="{colors["line"]}"/>')

    text(20, 32, year, 18, "blue")
    text(75, 32, "使った技術と活動時期", 18)
    as_of = date.fromisoformat(data["as_of"])
    text(780, 31, f"1/1–{as_of.month}/{as_of.day}", 11, "muted", 'text-anchor="end"')
    text(20, 59, "1マス＝1週", 11, "muted")
    # Label each week by the month containing its Thursday (same axis as the baseline).
    months = {}
    for week in range(count):
        thursday = week_start(year) + timedelta(days=week * 7 + 3)
        month = min(max(thursday, date(year, 1, 1)), date(year, 12, 31)).month
        months.setdefault(month, []).append(week)
    for month, weeks in months.items():
        text(x_track + (weeks[0] + weeks[-1]) * step / 2 + 4, 59, f"{month}月", 10, "muted", 'text-anchor="middle"')
    y = 70
    for group in data["groups"]:
        line(20, y, 780)
        text(20, y + 22, group["name"], 11, "muted")
        y += 8
        for row in group["rows"]:
            text(112, y + 14, row["name"])
            if row["weeks"] is None:
                text(x_track, y + 14, "時期未確認", 11, "muted")
                line(x_track + 72, y + 10, 778)
            else:
                through = date.fromisoformat(row["through"])
                last_week = week_index(through, year)
                active = set(row["weeks"])
                for week in range(count):
                    start = max(week_start(year) + timedelta(days=week * 7), date(year, 1, 1))
                    end = min(start + timedelta(days=6 - start.weekday()), date(year, 12, 31))
                    label = f'{row["name"]}・{start.month}/{start.day}–{end.month}/{end.day}'
                    x = x_track + week * step
                    if week > last_week:
                        svg.append(f'<circle cx="{x + 4}" cy="{y + 10}" r="1.5" fill="{colors["line"]}"><title>{escape(label)}：集計対象外・未確認</title></circle>')
                    else:
                        present = week in active
                        status = "コミット記録あり" if present else "記録なし"
                        fill = colors["blue" if present else "empty"]
                        svg.append(f'<rect x="{x}" y="{y + 6}" width="8" height="8" rx="1" fill="{fill}"><title>{escape(label)}：{status}（{through.isoformat()}まで確認）</title></rect>')
            y += 22
        y += 8
    line(20, y, 780)
    for x, color, label in ((20, "blue", "コミット記録あり"), (160, "empty", "記録なし"), (260, "line", "集計対象外・未確認")):
        if color == "line":
            svg.append(f'<circle cx="{x + 4}" cy="{y + 19}" r="1.5" fill="{colors[color]}"/>')
        else:
            svg.append(f'<rect x="{x}" y="{y + 15}" width="8" height="8" rx="1" fill="{colors[color]}"/>')
        text(x + 15, y + 23, label, 11, "muted")
    svg.append('</g></svg>')
    return "\n".join(svg) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(JST).date())
    parser.add_argument("--offline", action="store_true", help="Render the saved public activity without fetching GitHub")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    baseline = read_json(ROOT / "data/2026-baseline.json")
    saved_path = ROOT / "data/2026-activity.json"
    if args.offline:
        data = read_json(saved_path)
    else:
        sources = load_sources(ROOT / "data/sources.json", os.environ.get("TIMELINE_SOURCES_JSON", ""), {r["id"] for r in rows(baseline)})
        data = aggregate(baseline, sources, args.as_of, GitHub(os.environ.get("PROFILE_READ_TOKEN") or os.environ.get("GITHUB_TOKEN")))
        if saved_path.exists():
            prevent_regression(read_json(saved_path), data)
    # Complete API calls and render both themes before modifying any files.
    files = {"data/2026-activity.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
             "assets/2026/overview.svg": render_svg(data),
             "assets/2026/overview-dark.svg": render_svg(data, dark=True)}
    for name, content in files.items():
        path = args.output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print("Updated technology activity and both SVG themes.")


if __name__ == "__main__":
    try:
        main()
    except TimelineError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
