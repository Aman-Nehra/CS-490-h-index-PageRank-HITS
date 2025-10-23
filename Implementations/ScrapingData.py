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
    r = requests.get(f"{API_URL}{paper_id}?fields={FIELDS}", timeout=15)
    if r.status_code == 200:
        return r.json()
    else:
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

        # Add references 
        for ref in (data.get("references") or []):
            ref_id = ref.get("paperId")
            if ref_id and ref_id not in papers and len(papers) < max_nodes:
                queue.append(ref_id)

        # Add citations 
        for cit in (data.get("citations") or []):
            cit_id = cit.get("paperId")
            if cit_id and cit_id not in papers and len(papers) < max_nodes:
                queue.append(cit_id)

    return papers



def extract_edges(papers):
    out_edges = {}
    in_edges = {}

    for paper_id, paper in papers.items():
        # Get references and citations
        references = paper.get("references") or []
        citations = paper.get("citations") or []

        out_edges[paper_id] = []
        in_edges[paper_id] = []

        # Outgoing edges
        for ref in references:
            if ref and isinstance(ref, dict):
                ref_id = ref.get("paperId")
                if ref_id and ref_id in papers:  # keep only local edges
                    out_edges[paper_id].append(ref_id)
                    in_edges.setdefault(ref_id, []).append(paper_id)

        # Incoming edges
        for cit in citations:
            if cit and isinstance(cit, dict):
                cit_id = cit.get("paperId")
                if cit_id and cit_id in papers:
                    in_edges[paper_id].append(cit_id)
                    out_edges.setdefault(cit_id, []).append(paper_id)

    return out_edges, in_edges


def save_to_csv(papers, out_edges, in_edges, filename):
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paperId", "title", "references", "citations"])

        for paper_id, data in papers.items():
            refs = ";".join(out_edges.get(paper_id, []))
            cits = ";".join(in_edges.get(paper_id, []))
            title = data.get("title", "").replace("\n", " ").strip()
            writer.writerow([paper_id, title, refs, cits])

    print(f"\n CSV written to {filename} (nodes={len(papers)})")


def main():
    print("Starting Semantic Scholar subgraph collection...")
    papers = build_graph(SEED_PAPERS, MAX_NODES)
    out_edges, in_edges = extract_edges(papers)
    save_to_csv(papers, out_edges, in_edges, OUTPUT_CSV)


if __name__ == "__main__":
    main()
