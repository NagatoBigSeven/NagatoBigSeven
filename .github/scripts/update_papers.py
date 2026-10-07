"""Refresh owner-confirmed papers; author-name search is not identity evidence."""
from datetime import datetime
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Add IDs only after the owner confirms authorship.
CONFIRMED_IDS = ("2606.19152", "2606.05050", "2605.03205")
AUTHOR = "Zongmin Zhang"
NS = {"atom": "http://www.w3.org/2005/Atom"}
START, END = "<!-- PAPERS:START -->", "<!-- PAPERS:END -->"
REPO = Path(__file__).resolve().parents[2]


def paper_block(content):
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must have exactly one pair of PAPERS markers")
    start, end = content.index(START), content.index(END)
    if start >= end:
        raise ValueError("PAPERS markers are reversed")
    return start + len(START), end


def parse_existing(content):
    start, end = paper_block(content)
    statuses = {}
    for line in content[start:end].splitlines():
        parts = [part.strip() for part in re.split(r"(?<!\\)\|", line)]
        if len(parts) < 5:
            continue
        status_col = parts[3]
        match = re.search(r"arXiv:(\d{4}\.\d{5})", status_col)
        if match and "·" in status_col:
            statuses[match.group(1)] = status_col.split("·", 1)[0].strip()
    return statuses


def parse_feed(data):
    root = ET.fromstring(data)
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise ValueError("arXiv response is not an Atom feed")
    papers = {}
    for entry in root.findall("atom:entry", NS):
        id_url = entry.findtext("atom:id", default="", namespaces=NS)
        match = re.fullmatch(r"https?://(?:export\.)?arxiv\.org/abs/(\d{4}\.\d{5})(?:v\d+)?", id_url)
        if not match or match.group(1) not in CONFIRMED_IDS:
            raise ValueError("arXiv returned an unconfirmed paper or an error entry")
        paper_id = match.group(1)
        if paper_id in papers:
            raise ValueError("arXiv returned a duplicate paper")
        authors = {" ".join(author.findtext("atom:name", default="", namespaces=NS).split())
                   for author in entry.findall("atom:author", NS)}
        if AUTHOR not in authors:
            raise ValueError(f"Confirmed author missing from {paper_id}; inspect manually")
        title = " ".join(entry.findtext("atom:title", default="", namespaces=NS).split())
        published = entry.findtext("atom:published", default="", namespaces=NS)
        if not title:
            raise ValueError(f"Missing title for {paper_id}")
        date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError(f"Missing time zone for {paper_id}")
        papers[paper_id] = {"title": title, "arxiv_id": paper_id, "published": date}
    if set(papers) != set(CONFIRMED_IDS):
        raise ValueError("Incomplete arXiv response; keeping both existing README tables")
    return sorted(papers.values(), key=lambda paper: paper["published"], reverse=True)


def fetch_papers():
    query = urllib.parse.urlencode({"id_list": ",".join(CONFIRMED_IDS),
                                   "max_results": len(CONFIRMED_IDS)})
    request = urllib.request.Request(
        "https://export.arxiv.org/api/query?" + query,
        headers={"User-Agent": "NagatoBigSeven-GithubProfile/2.0 (mailto:zzmhkust@gmail.com)"})
    # Default HTTPS context verifies certificates; never disable it.
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_feed(response.read())


def build_table(papers, existing_statuses, is_cn=False):
    lines = ["| # | 论文标题 | 状态 |" if is_cn else "| # | Paper | Status |",
             "|:-:|:------|:------|"]
    for index, paper in enumerate(papers, 1):
        title = paper["title"].replace("\\", "\\\\").replace("|", "\\|")
        for char in "*_`[]<>":
            title = title.replace(char, "\\" + char)
        if ":" in title:
            prefix, suffix = title.split(":", 1)
            title = f"**{prefix.strip()}:** {suffix.strip()}"
        else:
            title = f"**{title}**"
        paper_id = paper["arxiv_id"]
        status = existing_statuses.get(paper_id, "")
        link = f"[arXiv:{paper_id}](https://arxiv.org/abs/{paper_id})"
        lines.append(f"| {index} | {title} | {status + ' · ' if status else ''}{link} |")
    return "\n".join(lines) + "\n"


def update_readmes(repo=REPO):
    files = [(Path(repo) / "README.md", False), (Path(repo) / "README_CN.md", True)]
    prepared = []
    for path, is_cn in files:
        content = path.read_text(encoding="utf-8")
        start, end = paper_block(content)
        prepared.append((path, content, start, end, is_cn, parse_existing(content)))
    papers = fetch_papers()
    for path, content, start, end, is_cn, statuses in prepared:
        result = content[:start] + "\n" + build_table(papers, statuses, is_cn) + content[end:]
        if result != content:
            path.write_text(result, encoding="utf-8")


def main():
    try:
        update_readmes()
    except Exception as error:
        print(f"Paper update failed: {error}", file=sys.stderr)
        return 1
    print("Confirmed paper metadata updated; review statuses remain owner-maintained.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
