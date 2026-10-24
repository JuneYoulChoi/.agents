"""Cross-check the published view, routing owners and inert candidate inventory."""

import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class OverviewParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


class DocumentationTests(unittest.TestCase):
    def test_every_active_skill_has_one_gate_and_existing_entry(self):
        registry = json.loads((ROOT / "registry/active-skills.json").read_text())
        routing = json.loads((ROOT / "registry/routing-gates.json").read_text())
        ids = [s["id"] for s in registry["skills"]]
        placed = [s for values in routing["skill_placement"].values() for s in values]
        self.assertCountEqual(ids, placed)
        self.assertEqual(len(placed), len(set(placed)))
        for skill in registry["skills"]:
            self.assertTrue(skill["entry"].startswith("skills/"))
            self.assertTrue((ROOT / skill["entry"]).is_file())
            self.assertTrue((ROOT / skill["entry"]).parent.joinpath("agents/openai.yaml").is_file())

    def test_candidate_inventory_is_complete_inert_and_matches_downloads(self):
        data = json.loads((ROOT / "registry/skill-candidate-review.json").read_text())
        paths = [p["path"] for p in data["packages"]]
        actual = {str(p.relative_to(ROOT)) for p in (ROOT / "incoming").glob("*/*/*")
                  if p.is_dir() and any(p.rglob("SKILL.md"))}
        self.assertEqual(set(paths), actual)
        self.assertEqual(len(paths), len(set(paths)))
        ids = {s["id"] for s in json.loads((ROOT / "registry/active-skills.json").read_text())["skills"]}
        for package in data["packages"]:
            root = ROOT / package["path"]
            hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(root.rglob("*")) if p.is_file()}
            digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
            self.assertEqual(digest, package["snapshot_sha256"], package["path"])
            self.assertFalse(package["runtime_activation"])
            self.assertTrue(set(package["core_coverage"]) <= ids)
            self.assertIn(package["disposition"], {"adapt_principles", "defer_package_review"})
            if "destination" in package:
                self.assertIn(package["destination"], ids)

    def test_markdown_source_links_resolve(self):
        documents = list((ROOT / "plan").glob("*.md"))
        documents += list((ROOT / "skills").rglob("*.md"))
        documents += [ROOT / "docs/harness/skill-adoption.md"]
        for path in documents:
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\s]+)\)", path.read_text()):
                if urlsplit(target).scheme or target.startswith("#"):
                    continue
                target = unquote(target.split("#", 1)[0])
                self.assertTrue((path.parent / target).exists(), f"{path.relative_to(ROOT)} -> {target}")

    def test_overview_has_current_layers_skills_and_local_links(self):
        path = ROOT / "docs/harness/index.html"
        text = path.read_text()
        parser = OverviewParser()
        parser.feed(text)
        parser.close()
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertIn('id="work-composition"', text)
        self.assertIn("2026-10-24", text)
        self.assertIn("5개 레이어", text)
        for skill in json.loads((ROOT / "registry/active-skills.json").read_text())["skills"]:
            self.assertIn(skill["id"].split(".", 1)[1], text)
        for link in parser.links:
            self.assertFalse(urlsplit(link).scheme, link)
            if link.startswith("#"):
                self.assertIn(link[1:], parser.ids)
            else:
                self.assertTrue((path.parent / unquote(link.split("#", 1)[0])).exists(), link)

    def test_no_deep_only_delegation_policy_or_incoming_runtime_links(self):
        for path in list((ROOT / "plan").glob("*.md")):
            text = path.read_text()
            self.assertNotRegex(text, r"only for Deep mode|MAY for Deep|Parallel experts are a Deep-mode")
        for path in (ROOT / "skills").rglob("*.md"):
            self.assertNotRegex(path.read_text(), r"\]\([^)]*incoming/")
