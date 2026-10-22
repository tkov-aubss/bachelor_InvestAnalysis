#!/usr/bin/env python3
import os
import pandas as pd
import regex as re
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR  = os.path.join(BASE_DIR, "data", "crypto")

def read_year_file(fname):
    path = os.path.join(CSV_DIR, fname)
    try:
        df = pd.read_csv(path, parse_dates=["datetime"], low_memory=False)
    except (pd.errors.ParserError, UnicodeDecodeError):
        df = pd.read_csv(path, parse_dates=["datetime"], engine="python")
    if "date" in df.columns:
        df = df.drop(columns=["date"])
    return df

def clean_tweet_fast(text: str) -> str:
    cleaned = re.sub(r"(@\w+)|(http\S+)|([^A-Za-z \t])", " ", str(text))
    return " ".join(cleaned.split()).lower()

def main():
    # 1) Načítanie CSV
    df1 = read_year_file("bitcoin-tweets-2021.csv")
    df2 = read_year_file("bitcoin-tweets-2022.csv")

    # 2) Bez duplicitných názvov stĺpcov
    df1 = df1.loc[:, ~df1.columns.duplicated()]
    df2 = df2.loc[:, ~df2.columns.duplicated()]

    # 3) Spojenie a zoradenie
    tweets = pd.concat([df1, df2], ignore_index=True, sort=False)
    tweets = tweets.sort_values("datetime").reset_index(drop=True)
    print(f"Loaded {len(tweets)} tweets total.")

    # 4) Filtrovanie heavy users
    tweets = tweets.groupby("username").filter(lambda g: len(g) < 1000)
    print(f"After filtering heavy users: {len(tweets)}")

    # 5) Čistenie textu
    tweets["text_clean"] = tweets["text"].map(clean_tweet_fast)

    # 6) Odstránenie duplicitných čistých tweetov
    tweets = tweets.drop_duplicates(subset=["text_clean"]).reset_index(drop=True)
    print(f"After deduplication: {len(tweets)}")

    # 7) Rozdelenie na 20 častí
    parts = np.array_split(tweets, 20)

    # 8) Uloženie každej časti po 100 000 záznamoch (resp. 1 000 000)
    chunk_size = 100_000  # nastavte na 1_000_000 ak chcete veľké dávky
    for part_idx, df_part in enumerate(parts, start=1):
        # ak chcete navyše spracovať po dávkach v rámci každej časti:
        for start in range(0, len(df_part), chunk_size):
            chunk = df_part.iloc[start : start + chunk_size]
            fname = f"bitcoin_tweets_part{part_idx}_rows{start+1}-{start+len(chunk)}.csv"
            out_path = os.path.join(BASE_DIR, fname)
            chunk.to_csv(out_path, index=False)
            print(f"Saved {len(chunk)} rows of part {part_idx} to {fname}")

if __name__ == "__main__":
    main()
