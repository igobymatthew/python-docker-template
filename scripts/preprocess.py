import argparse
import pandas as pd
import re
import unicodedata
import ftfy
from cleantext import clean
from pathlib import Path

LABELS = [
    "identity_attack",
    "insult",
    "obscene",
    "severe_toxicity",
    "sexual_explicit",
    "threat",
    "toxicity",
]

def clean_text(text: str) -> str:
    text = ftfy.fix_text(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r">.*\n", "", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\b(?:u/|@)\w+", "", text)
    text = clean(text, fix_unicode=False, lower=False, no_urls=True, no_emails=True)
    return text.strip()

def preprocess(input_file: str, output_file: str) -> None:
    df = pd.read_csv(input_file)
    if "text" not in df.columns:
        raise ValueError("Input file must contain a 'text' column")
    df["text"] = df["text"].astype(str).apply(clean_text)
    df.to_csv(output_file, index=False)
    print(f"Preprocessed data saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and normalize text data")
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    preprocess(args.input_file, args.output_file)
