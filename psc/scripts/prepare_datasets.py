"""Download and pre-process the six real-world datasets of the paper (Table 1)
into the unified format of Appendix A.

Dataset      |V|  |E|   Source
CU            49  107   KONECT  contiguous-usa
Do            62  159   KONECT  dolphins
ML            77  254   KONECT  moreno_lesmis  (networkx built-in copy)
CS            86  124   Network Repository  ca-sandi_auths
EE           143  623   Network Repository  email-enron-only
PM           453 2025   KONECT  arenas-meta (C. elegans metabolic)

Usage::

    python scripts/prepare_datasets.py [--raw data/raw] [--out data]
"""

from __future__ import annotations

import argparse
import io
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from psc.graph import Graph, build_records, relabel_edges, save_records  # noqa: E402

SOURCES = {
    "CU": ("konect", "http://konect.cc/files/download.tsv.contiguous-usa.tar.bz2", "out.contiguous-usa"),
    "Do": ("konect", "http://konect.cc/files/download.tsv.dolphins.tar.bz2", "out.dolphins"),
    "ML": ("networkx", None, None),
    "CS": ("nrvis", "https://nrvis.com/download/data/ca/ca-sandi_auths.zip", "ca-sandi_auths.mtx"),
    "EE": ("nrvis", "https://nrvis.com/download/data/email/email-enron-only.zip", "email-enron-only.mtx"),
    "PM": ("konect", "http://konect.cc/files/download.tsv.arenas-meta.tar.bz2", "out.arenas-meta"),
}

EXPECTED = {"CU": (49, 107), "Do": (62, 159), "ML": (77, 254), "CS": (86, 124), "EE": (143, 623), "PM": (453, 2025)}

FULL_NAMES = {
    "CU": "Contiguous USA",
    "Do": "Dolphins",
    "ML": "Les Miserables",
    "CS": "Ca-sandi_auths",
    "EE": "Email-enron-only",
    "PM": "Caenorhabditis elegans",
}


def _download(url: str, cache: Path) -> bytes:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return cache.read_bytes()
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
        data = resp.read()
    cache.write_bytes(data)
    return data


def _parse_edge_lines(text: str) -> list[tuple[int, int]]:
    """Parse KONECT ``out.*`` / MatrixMarket ``.mtx`` edge lists."""
    edges = []
    header_seen = False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("%") or line.startswith("#"):
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        # MatrixMarket size header "n n m" (three ints, appears once first)
        if not header_seen and len(parts) == 3 and parts[0] == parts[1]:
            header_seen = True
            continue
        header_seen = True
        edges.append((int(parts[0]), int(parts[1])))
    return edges


def load_raw_edges(name: str, raw_dir: Path) -> list[tuple[int, int]]:
    kind, url, member = SOURCES[name]
    if kind == "networkx":
        import networkx as nx

        g = nx.les_miserables_graph()
        return list(g.edges())
    data = _download(url, raw_dir / Path(url).name)
    if kind == "konect":
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:bz2") as tar:
            for m in tar.getmembers():
                if m.name.endswith(member):
                    text = tar.extractfile(m).read().decode("utf-8", errors="ignore")
                    return _parse_edge_lines(text)
    if kind == "nrvis":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for m in zf.namelist():
                if m.endswith(member):
                    text = zf.read(m).decode("utf-8", errors="ignore")
                    return _parse_edge_lines(text)
    raise RuntimeError(f"member {member} not found for {name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data")
    ap.add_argument("--datasets", default="CU,Do,ML,CS,EE,PM")
    args = ap.parse_args()

    raw_dir, out_dir = Path(args.raw), Path(args.out)
    print(f"{'Dataset':<8}{'|V|':>6}{'|E|':>7}{'dmax':>6}{'avg-deg':>9}{'2-star':>8}{'3-star':>8}{'triangle':>10}")
    for name in args.datasets.split(","):
        raw = load_raw_edges(name, raw_dir)
        n, edges = relabel_edges(raw)
        g = Graph.from_edges(n, edges)
        exp_n, exp_m = EXPECTED[name]
        flag = "" if (g.n, g.m) == (exp_n, exp_m) else f"  (paper: {exp_n}/{exp_m})"
        print(
            f"{name:<8}{g.n:>6}{g.m:>7}{g.max_degree():>6}{g.average_degree():>9.4f}"
            f"{g.count_kstars(2):>8}{g.count_kstars(3):>8}{g.count_triangles():>10}{flag}",
        )
        save_records(build_records(name, g), out_dir / f"{name}.json")
    print(f"saved to {out_dir}/")


if __name__ == "__main__":
    main()
