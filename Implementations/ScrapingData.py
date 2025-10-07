import requests
import csv

API_URL = "https://api.semanticscholar.org/graph/v1/paper/"
FIELDS = "title,references.paperId,citations.paperId"

# choose highly cited papers as seeds (dense connectivity)
SEED_PAPERS = [
    "arXiv:1706.03762",  # Attention Is All You Need
    "arXiv:1409.0473",   # ResNet
    "arXiv:1312.5602",   # AlexNet
]

MAX_NODES = 150
SLEEP_TIME = 0.6  # seconds between API calls to avoid rate limit
OUTPUT_CSV = "papers.csv"

def fetch_paper(paper_id):
    try:
        r = requests.get(f"{API_URL}{paper_id}?fields={FIELDS}", timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception:
        return None


def build_graph(seed_papers, max_nodes=100):
    papers = {}
    queue = list(seed_papers)

    while queue and len(papers) < max_nodes:
        paper_id = queue.pop(0)
        if paper_id in papers:
            continue

        data = fetch_paper(paper_id)
        if not data:
            continue

        papers[paper_id] = data

        # Add references (papers that this one cites)
        for ref in (data.get("references") or []):
            rid = ref.get("paperId")
            if rid and rid not in papers and len(papers) < max_nodes:
                queue.append(rid)

        # Add citations (papers that cite this one)
        for cit in (data.get("citations") or []):
            cid = cit.get("paperId")
            if cid and cid not in papers and len(papers) < max_nodes:
                queue.append(cid)

    return papers



def extract_edges(papers):
    out_edges = {}
    in_edges = {}

    for pid, paper in papers.items():
        # Get references (papers that this paper cites)
        references = paper.get("references") or []
        citations = paper.get("citations") or []

        out_edges[pid] = []
        in_edges[pid] = []

        # Outgoing edges: from this paper to the ones it cites
        for ref in references:
            if ref and isinstance(ref, dict):
                rid = ref.get("paperId")
                if rid and rid in papers:  # keep only local edges
                    out_edges[pid].append(rid)
                    in_edges.setdefault(rid, []).append(pid)

        # Incoming edges: from papers that cite this paper
        for cit in citations:
            if cit and isinstance(cit, dict):
                cid = cit.get("paperId")
                if cid and cid in papers:
                    in_edges[pid].append(cid)
                    out_edges.setdefault(cid, []).append(pid)

    return out_edges, in_edges


def save_to_csv(papers, out_edges, in_edges, filename):
    """Write all data to a single CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paperId", "title", "references", "citations"])

        for pid, data in papers.items():
            refs = ";".join(out_edges.get(pid, []))
            cits = ";".join(in_edges.get(pid, []))
            title = data.get("title", "").replace("\n", " ").strip()
            writer.writerow([pid, title, refs, cits])

    print(f"\n✅ CSV written to {filename} (nodes={len(papers)})")


def main():
    print("Starting Semantic Scholar subgraph collection...")
    papers = build_graph(SEED_PAPERS, MAX_NODES)
    out_edges, in_edges = extract_edges(papers)
    save_to_csv(papers, out_edges, in_edges, OUTPUT_CSV)


if __name__ == "__main__":
    main()
