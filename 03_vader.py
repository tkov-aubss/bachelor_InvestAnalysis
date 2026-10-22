#!/usr/bin/env python3
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 1. Configuration
DATE_START = "2021-01-01"
DATE_END   = "2022-09-30"

FILES = [
    {
        "path": "/Users/tomaskovac/Desktop/BC/Python/DATA/bitcoin_merged.csv",
        "date_col": "datetime",   # your file uses "Date" not "Data"
        "text_col": "text",
        "out_csv": "bitcoin_with_vader.csv"
    }
]

def load_and_filter(path, date_col):
    """
    Read a CSV, parse the `date_col`, then filter to DATE_START<=date<=DATE_END.
    Falls back to engine='python' if the C engine errors.
    """
    try:
        df = pd.read_csv(
            path,
            parse_dates=[date_col]
        )
    except (pd.errors.ParserError, UnicodeDecodeError):
        # fallback for large/malformed files
        df = pd.read_csv(
            path,
            parse_dates=[date_col],
            engine="python"
        )
    # filter by date
    mask = (df[date_col] >= DATE_START) & (df[date_col] <= DATE_END)
    return df.loc[mask].copy()

def add_vader(df, text_col):
    """
    Apply VADER to the specified text column and return df with
    neg/neu/pos/compound columns appended.
    """
    analyzer = SentimentIntensityAnalyzer()
    # ensure strings (avoid nan issues)
    texts = df[text_col].astype(str)
    scores = texts.apply(analyzer.polarity_scores)
    return pd.concat([df, pd.DataFrame(list(scores))], axis=1)

def main():
    for cfg in FILES:
        print(f"→ Processing {cfg['path']} …")
        df = load_and_filter(cfg["path"], cfg["date_col"])
        print(f"   Rows in {DATE_START}→{DATE_END}: {len(df)}")
        df = add_vader(df, cfg["text_col"])
        df.to_csv(cfg["out_csv"], index=False)
        print(f"   Saved enriched CSV to {cfg['out_csv']}\n")

if __name__ == "__main__":
    main()
