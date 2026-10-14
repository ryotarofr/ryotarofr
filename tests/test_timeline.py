import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

from scripts import update_timeline as timeline


def commit(stamp, login="ryotarofr", kind="User"):
    return {"author": {"login": login, "type": kind}, "commit": {"committer": {"date": stamp}}}


class FakeGitHub:
    def __init__(self, commits):
        self.data = commits
        self.calls = []

    def commits(self, source, author, start, end):
        self.calls.append((source, author, start, end))
        return self.data


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {"year": 2026, "author": "ryotarofr", "through": "2026-10-14", "groups": [
            {"name": "Web・API", "rows": [
                {"id": "known", "name": "Known", "weeks": [0, 41]},
                {"id": "unknown", "name": "FastAPI", "weeks": None}]}]}
        self.source = {"repo": "owner/private-name", "technologies": ["known"]}

    def test_jst_week_boundary_author_filter_and_deduplication(self):
        github = FakeGitHub([
            commit("2026-10-18T14:59:59Z"),  # Sunday JST, week 41
            commit("2026-10-18T15:00:00Z"),  # Monday JST, week 42
            commit("2026-10-18T15:00:00Z"),
            commit("2026-10-25T15:00:00Z", login="other"),
            commit("2026-10-25T15:00:00Z", kind="Bot"),
            commit("2026-10-11T15:00:00Z"),  # Before automatic collection starts
            commit("2026-11-01T15:00:00Z"),  # Outside the requested end date
        ])
        result = timeline.aggregate(self.baseline, [self.source], date(2026, 10, 31), github)
        known, unknown = timeline.rows(result)
        self.assertEqual(known["weeks"], [0, 41, 42])
        self.assertEqual(known["through"], "2026-10-31")
        self.assertIsNone(unknown["weeks"])
        self.assertEqual(github.calls[0][2:], (date(2026, 10, 15), date(2026, 10, 31)))
        self.assertEqual(self.baseline["groups"][0]["rows"][0]["weeks"], [0, 41])

    def test_new_year_and_year_end(self):
        self.assertEqual(timeline.week_index(date(2026, 1, 1), 2026), 0)
        self.assertEqual(timeline.week_index(date(2026, 1, 5), 2026), 1)
        self.assertEqual(timeline.week_index(date(2026, 12, 31), 2026), 52)
        github = FakeGitHub([commit("2026-12-31T14:59:59Z"), commit("2026-12-31T15:00:00Z")])
        result = timeline.aggregate(self.baseline, [self.source], date(2027, 1, 2), github)
        self.assertEqual(result["as_of"], "2026-12-31")
        self.assertEqual(timeline.rows(result)[0]["weeks"], [0, 41, 52])

    def test_unknown_dates_need_an_actual_commit(self):
        source = dict(self.source, technologies=["unknown"], since="2026-01-01", until="2026-01-31")
        empty = timeline.aggregate(self.baseline, [source], date(2026, 10, 15), FakeGitHub([]))
        self.assertIsNone(timeline.rows(empty)[1]["weeks"])
        found = timeline.aggregate(self.baseline, [source], date(2026, 10, 15), FakeGitHub([commit("2026-01-04T15:00:00Z")]))
        self.assertEqual(timeline.rows(found)[1]["weeks"], [1])
        self.assertEqual(timeline.rows(found)[1]["through"], "2026-01-31")

    def test_unmapped_rows_keep_their_original_cutoff(self):
        result = timeline.aggregate(self.baseline, [], date(2026, 12, 1), FakeGitHub([]))
        self.assertEqual(timeline.rows(result)[0]["through"], "2026-10-14")
        svg = timeline.render_svg(result)
        self.assertIn("10/19–10/25：集計対象外・未確認", svg)

    def test_shared_source_is_fetched_once(self):
        github = FakeGitHub([commit("2026-10-18T15:00:00Z")])
        sources = [self.source, dict(self.source, technologies=["unknown"])]
        timeline.aggregate(self.baseline, sources, date(2026, 10, 20), github)
        self.assertEqual(len(github.calls), 1)

    def test_pagination_and_api_filters(self):
        github = timeline.GitHub(None)
        source = dict(self.source, path="app/with spaces", ref="feature/test")
        with patch.object(github, "request", side_effect=[[{}] * 100, [{}] * 2]) as request:
            result = list(github.commits(source, "ryotarofr", date(2026, 1, 1), date(2026, 1, 2)))
        self.assertEqual(len(result), 102)
        queries = [parse_qs(urlparse(call.args[0]).query) for call in request.call_args_list]
        self.assertEqual([query["page"] for query in queries], [["1"], ["2"]])
        self.assertEqual(queries[0]["author"], ["ryotarofr"])
        self.assertEqual(queries[0]["since"], ["2026-01-01T00:00:00+09:00"])
        self.assertEqual(queries[0]["until"], ["2026-01-02T23:59:59+09:00"])
        self.assertEqual(queries[0]["path"], ["app/with spaces"])
        self.assertEqual(queries[0]["sha"], ["feature/test"])

    def test_invalid_private_config_does_not_echo_its_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            path.write_text("[]", encoding="utf-8")
            for invalid in ['{"private-name":true}', '[{"repo":"private-name"}]', '[{"repo":"owner/private-name","technologies":["typo"]}]']:
                with self.subTest(config=invalid), self.assertRaises(timeline.TimelineError) as error:
                    timeline.load_sources(path, invalid, {"known"})
                self.assertNotIn("private-name", str(error.exception))
            sources = timeline.load_sources(path, json.dumps([self.source]), {"known"})
            self.assertEqual(sources, [self.source])

    def test_missing_secret_or_rewritten_history_cannot_erase_activity(self):
        previous = timeline.aggregate(self.baseline, [self.source], date(2026, 10, 20), FakeGitHub([commit("2026-10-18T15:00:00Z")]))
        missing = timeline.aggregate(self.baseline, [], date(2026, 10, 21), FakeGitHub([]))
        rewritten = timeline.aggregate(self.baseline, [self.source], date(2026, 10, 21), FakeGitHub([]))
        for current in (missing, rewritten):
            with self.assertRaises(timeline.TimelineError):
                timeline.prevent_regression(previous, current)
        timeline.prevent_regression(previous, copy.deepcopy(previous))

    def test_api_failure_leaves_all_output_files_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ("data/2026-activity.json", "assets/2026/overview.svg", "assets/2026/overview-dark.svg"):
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("previous", encoding="utf-8")
            with patch("sys.argv", ["update", "--as-of", "2026-10-15", "--output-dir", directory]), patch.object(timeline.GitHub, "request", side_effect=timeline.TimelineError("API failed")), patch.dict("os.environ", {"TIMELINE_SOURCES_JSON": ""}):
                with self.assertRaises(timeline.TimelineError):
                    timeline.main()
            self.assertTrue(all(path.read_text(encoding="utf-8") == "previous" for path in output.rglob("*") if path.is_file()))

    def test_both_svgs_are_valid_and_do_not_contain_private_sources(self):
        self.baseline["groups"][0]["rows"][0]["name"] = "A & <B>"
        result = timeline.aggregate(self.baseline, [self.source], date(2026, 10, 15), FakeGitHub([]))
        self.assertNotIn("private-name", json.dumps(result))
        for dark in (False, True):
            svg = timeline.render_svg(result, dark)
            ET.fromstring(svg)
            self.assertNotIn("private-name", svg)
            self.assertIn("A &amp; &lt;B&gt;", svg)
            self.assertIn("時期未確認", svg)


if __name__ == "__main__":
    unittest.main()
