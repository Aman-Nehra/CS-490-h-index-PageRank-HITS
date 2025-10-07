# ScrapingAuthorsData.py
import requests
import csv
import time

API_URL = "https://api.semanticscholar.org/graph/v1/paper/"
FIELDS_PAPER = "title,references.paperId,citations.paperId,authors.authorId,authors.name"
SEED_PAPERS = [
    "arXiv:1706.03762",  # Attention Is All You Need
    "arXiv:1409.0473",   # ResNet
    "arXiv:1312.5602",   # AlexNet
]
MAX_PAPERS = 50
SLEEP_TIME = 1.0
OUTPUT_CSV = "authors_papers.csv"

# ----------------------------
# Fetch paper from Semantic Scholar
# ----------------------------
def fetch_paper(paper_id):
    try:
        r = requests.get(f"{API_URL}{paper_id}?fields={FIELDS_PAPER}", timeout=15)
        if r.status_code == 200:
            print(f"✅ Fetched {paper_id}")
            return r.json()
        else:
            print(f"⚠️ Failed {paper_id}, status={r.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Exception fetching {paper_id}: {e}")
        return None

# ----------------------------
# Build paper graph and collect papers
# ----------------------------
def build_paper_graph(seed_papers, max_papers=20):
    papers = {}
    queue = list(seed_papers)
    while queue and len(papers) < max_papers:
        pid = queue.pop(0)
        if pid in papers:
            continue
        data = fetch_paper(pid)
        if not data:
            continue
        papers[pid] = data
        # Add references
        for ref in data.get("references") or []:
            rid = ref.get("paperId")
            if rid and rid not in papers and len(papers) < max_papers:
                queue.append(rid)
        # Add citations
        for cit in data.get("citations") or []:
            cid = cit.get("paperId")
            if cid and cid not in papers and len(papers) < max_papers:
                queue.append(cid)
        time.sleep(SLEEP_TIME)
    print(f"\n✅ Total papers fetched: {len(papers)}")
    return papers

# ----------------------------
# Save papers and authors to CSV
# ----------------------------
def save_to_csv(papers, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paperId", "title", "authors", "references", "citations"])
        for pid, data in papers.items():
            title = data.get("title","").replace("\n"," ").strip()
            authors = ";".join([f"{a.get('authorId')}:{a.get('name','Unknown')}" for a in data.get("authors") or [] if a.get("authorId")])
            refs = ";".join([r.get("paperId") for r in data.get("references") or [] if r.get("paperId")])
            cits = ";".join([c.get("paperId") for c in data.get("citations") or [] if c.get("paperId")])
            writer.writerow([pid, title, authors, refs, cits])
    print(f"✅ CSV saved to {filename}")

# ----------------------------
# MAIN
# ----------------------------
def main():
    print("Starting Semantic Scholar scraping...")
    papers = build_paper_graph(SEED_PAPERS, MAX_PAPERS)
    save_to_csv(papers, OUTPUT_CSV)

if __name__ == "__main__":
    main()
