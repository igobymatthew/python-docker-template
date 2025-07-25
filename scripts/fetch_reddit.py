import argparse
import json
import os
from pathlib import Path
import urllib.request


def fetch(subreddit: str, limit: int = 100, out_dir: str = "data/external") -> None:
    url = f"https://api.pushshift.io/reddit/comment/search/?subreddit={subreddit}&size={limit}"
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"{subreddit}.jsonl"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    with path.open("w", encoding="utf-8") as f:
        for item in data.get("data", []):
            json.dump(item, f)
            f.write("\n")
    print(f"Saved {len(data.get('data', []))} records to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Reddit comments via Pushshift")
    parser.add_argument("--subreddit", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--out_dir", default="data/external")
    args = parser.parse_args()
    fetch(args.subreddit, args.limit, args.out_dir)
