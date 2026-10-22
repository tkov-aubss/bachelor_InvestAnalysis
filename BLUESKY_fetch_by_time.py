#!/usr/bin/env python3
# fetch_by_time_debug_v3.py

import os
import json
import time
import logging
import sys # To check if output is a terminal for \r
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from atproto import Client, models
from collections import Counter

# Assuming config.py is in the same directory or Python path
from config import (
    # Import STOCKS/CRYPTO for type checking in mk_query
    STOCKS, CRYPTO, ASSETS,
    MONTHLY_TARGET, HANDLE, APP_PWD,
    OUTPUT_DIR, LOG_FILE, RATE_SLEEP, BACKOFF, FETCH_LIMIT_PER_PAGE
)

# --- Setup Logging ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG) # Capture all levels

# File Handler - Captures DEBUG and above
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Console Handler - Shows INFO and above
console_handler = logging.StreamHandler(sys.stdout) # Use stdout
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Check if sys.stdout is a terminal (supports \r)
is_terminal = sys.stdout.isatty()
# --- End Logging Setup ---


def month_ranges(start_dt, end_dt):
    """Yield the first-of-month datetime for each month in [start..end]."""
    cur = datetime(start_dt.year, start_dt.month, 1, tzinfo=timezone.utc)
    end_month_start = datetime(end_dt.year, end_dt.month, 1, tzinfo=timezone.utc)
    while cur <= end_month_start:
        yield cur
        cur += relativedelta(months=1)

# --- REVERTED mk_query definition ---
# Uses only the primary asset ID to build the query
def mk_query(asset: str) -> str:
    """Lucene query: "$TICKER" OR "TICKER" for stocks, just "TICKER" for crypto, English only."""
    # Check if the primary asset ID belongs to a stock entry in config.ASSETS
    # We need to compare asset against the first element of each list in STOCKS
    # Ensure the inner list is not empty before accessing index 0
    is_stock = any(asset == stock_list[0] for stock_list in STOCKS if stock_list)

    if is_stock:
        # Use the primary asset ID for the query terms "$ASSET" OR "ASSET"
        term = f'"${asset}" OR "{asset}"'
    else:
        # For crypto, just use the primary asset ID "ASSET"
        term = f'"{asset}"'
    return f'{term} lang:en'
# --- End REVERTED mk_query definition ---


def aturi_to_url(uri: str) -> str:
    """Convert at://… URI to https://bsky.app/profile/…/post/… URL."""
    try:
        did, coll, rkey = uri[len("at://"):].split("/", 2)
        if coll == "app.bsky.feed.post":
            return f"https://bsky.app/profile/{did}/post/{rkey}"
    except ValueError:
        pass
    return uri

def split_header_body(text: str):
    """Splits text into header (first line) and body (rest)."""
    parts = text.split("\n", 1)
    header = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    return header, body

# Adjusted fetch_month signature slightly - search_terms no longer directly used for query
def fetch_month(client: Client, asset_id: str, search_terms: list[str], month_start: datetime, target: int):
    """
    Fetch up to `target` posts for a given asset (using asset_id for query) and month,
    logging rejections and reasons. Accepts posts with header only.
    Provides cleaner console output.
    Returns accepted posts, rejected posts with reasons, and rejection stats.
    Note: search_terms is passed but only asset_id is used for mk_query now.
    """
    # --- REVERTED query generation: Use the primary asset_id ---
    q = mk_query(asset_id)
    # --- End REVERTED query generation ---

    month_end = month_start + relativedelta(months=1)
    until_iso = month_end.isoformat().replace('+00:00', 'Z')

    accepted_posts = []
    rejected_posts = []
    rejection_counts = Counter()
    seen_uris = set()
    cursor = None
    pages_fetched = 0
    MAX_PAGES_PER_MONTH = 500 # Safety break

    # Console: Show starting message for the month using asset_id
    logging.info(f"→ Fetching {asset_id} {month_start.strftime('%Y-%m')}: Target {target}")

    last_progress_len = 0 # For clearing the line with \r

    while len(accepted_posts) < target and pages_fetched < MAX_PAGES_PER_MONTH:
        params = models.AppBskyFeedSearchPosts.Params(
            q=q, sort='latest', limit=FETCH_LIMIT_PER_PAGE,
            until=until_iso, cursor=cursor
        )

        raw_posts_on_page = 0
        try:
            # Log API call attempt only to file, including the query used
            logging.debug(f"   Fetching page {pages_fetched + 1} for query: {q}...")
            resp = client.app.bsky.feed.search_posts(params=params)
            pages_fetched += 1
            raw_posts_on_page = len(resp.posts)
            logging.debug(f"   Page {pages_fetched}: Fetched {raw_posts_on_page} raw. Cursor: {resp.cursor is not None}.")

        except Exception as e:
            rejection_counts['api_error'] += 1
            # Show API errors on console
            logging.warning(f"\n   ⚠️ API Error/Rate Limit: {e}. Backing off {RATE_SLEEP * BACKOFF}s...")
            time.sleep(RATE_SLEEP * BACKOFF)
            continue # Retry

        if not resp.posts:
            logging.debug("   API returned empty posts list.")
            # Console: Show end reason clearly
            if is_terminal: print(f"\r{' ' * last_progress_len}\r", end="") # Clear previous progress line
            logging.info("   ↳ No more posts returned by API for this period.")
            break

        kept_this_page = 0
        for p in resp.posts:
            rejection_reason = None

            # --- Validity Checks (Log details only to file) ---
            if not isinstance(p, models.AppBskyFeedDefs.PostView):
                rejection_reason = 'invalid_post_object'; rejection_counts[rejection_reason] += 1
                logging.debug(f"      Rejected {getattr(p, 'uri', 'N/A')}: {rejection_reason}")
                continue
            uri = p.uri
            if uri in seen_uris:
                rejection_reason = 'duplicate_uri_this_run'; rejection_counts[rejection_reason] += 1
                logging.debug(f"      Rejected {uri}: {rejection_reason}")
                continue
            if not p.record or not hasattr(p.record, 'text'):
                rejection_reason = 'no_text_record'; rejection_counts[rejection_reason] += 1
                logging.debug(f"      Rejected {uri}: {rejection_reason}")
                rejected_posts.append({"uri": uri, "reason": rejection_reason, "indexedAt": p.indexed_at})
                continue

            # --- Timestamp Check (Log details only to file) ---
            try:
                ts_str = p.indexed_at if isinstance(p.indexed_at, str) else p.indexed_at.isoformat()
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).astimezone(timezone.utc)
            except Exception as ts_e:
                rejection_reason = 'timestamp_parse_error'; rejection_counts[rejection_reason] += 1
                logging.warning(f"      Timestamp parse error for {uri}: {ts_e}") # Warning for potential data issue
                rejected_posts.append({"uri": uri, "reason": rejection_reason, "indexedAt_raw": p.indexed_at})
                continue

            if not (month_start <= ts < month_end):
                rejection_reason = 'outside_month_range'; rejection_counts[rejection_reason] += 1
                logging.debug(f"      Rejected {uri}: {rejection_reason} (Timestamp: {ts.isoformat()})")
                rejected_posts.append({"uri": uri, "reason": rejection_reason, "indexedAt": ts.isoformat()})
                continue

            # --- Content Filtering (Log details only to file) ---
            text = (p.record.text or "").strip()
            if not text:
                rejection_reason = 'empty_text_content'; rejection_counts[rejection_reason] += 1
                logging.debug(f"      Rejected {uri}: {rejection_reason}")
                rejected_posts.append({"uri": uri, "reason": rejection_reason, "indexedAt": ts.isoformat()})
                continue

            header, body = split_header_body(text)

            # --- Accept Post ---
            seen_uris.add(uri)
            kept_this_page += 1
            accepted_posts.append({
                "user": p.author.handle, "header": header, "body": body,
                "comments": p.reply_count or 0, "reposts": p.repost_count or 0, "likes": p.like_count or 0,
                "uri": uri, "url": aturi_to_url(uri), "indexedAt": ts.isoformat()
            })

            # --- Console Progress Update (on the same line) ---
            progress_text = f"   Progress: {len(accepted_posts)}/{target} accepted (Page {pages_fetched})"
            if is_terminal:
                print(f"\r{progress_text}{' ' * (last_progress_len - len(progress_text))}", end="")
                last_progress_len = len(progress_text)
            # --- End Console Progress Update ---

            if len(accepted_posts) >= target:
                break # Stop processing this page if target met

        logging.debug(f"   Page {pages_fetched}: Kept {kept_this_page} posts.")

        if len(accepted_posts) >= target:
            if is_terminal: print(f"\r{' ' * last_progress_len}\r", end="") # Clear progress line
            logging.info("   ✨ Target met for this month.")
            break

        cursor = resp.cursor
        if not cursor:
            logging.debug("   API returned no cursor.")
            if is_terminal: print(f"\r{' ' * last_progress_len}\r", end="") # Clear progress line
            # Console: Show end reason clearly
            logging.info("   ↳ Reached end of results for this query/timespan (no cursor).")
            break

        time.sleep(RATE_SLEEP)

    # End of month processing - ensure final status is on a new line
    if is_terminal and last_progress_len > 0:
         print() # Move to next line after finishing \r updates

    if pages_fetched >= MAX_PAGES_PER_MONTH:
        logging.warning(f"   ⚠️ Reached max pages ({MAX_PAGES_PER_MONTH}) for this month.")
    logging.info(f"   Finished {month_start.strftime('%Y-%m')}. Accepted: {len(accepted_posts)}")
    logging.info(f"   Rejection stats this month: {dict(rejection_counts)}") # Show summary on console

    return accepted_posts, rejected_posts, rejection_counts

def main():
    if not HANDLE or not APP_PWD or HANDLE == "your_handle" or APP_PWD == "your_password":
        logging.error("CRITICAL: Bsky HANDLE and APP_WD not set correctly in config.py or environment variables.")
        sys.exit("BSKY_HANDLE and BSKY_APP_PWD must be set. Please check config.py or environment variables.")


    rejected_dir = os.path.join(OUTPUT_DIR, "rejected")
    for sub in ("stocks", "crypto"):
        os.makedirs(os.path.join(OUTPUT_DIR, sub), exist_ok=True)
    os.makedirs(rejected_dir, exist_ok=True)

    logging.info("Attempting login...")
    client = Client(base_url='https://bsky.social')
    try:
        client.login(HANDLE, APP_PWD)
        logging.info(f"✅ Login successful as {HANDLE}")
    except Exception as login_err:
        logging.exception("❌ Login failed:")
        return

    START_DATE = datetime(2023, 1, 1, tzinfo=timezone.utc)
    END_DATE   = datetime(2024, 12, 31, tzinfo=timezone.utc)

    logging.info(f"🚀 Starting data fetch for {len(ASSETS)} assets from {START_DATE.date()} to {END_DATE.date()}...")
    logging.info(f"Targeting ~{MONTHLY_TARGET} posts per asset per month for acceptance.")
    logging.info(f"ℹ️ Detailed logs saved to: {LOG_FILE}")
    logging.info(f"ℹ️ Posts with only a header are ACCEPTED.")

    overall_rejection_stats = Counter()

    # Iterate through the list of lists in ASSETS
    for asset_data in ASSETS:
        # Extract primary ID and the list of search terms
        if not asset_data or not isinstance(asset_data, list):
            logging.warning(f"Skipping invalid asset entry in config: {asset_data}")
            continue
        primary_asset_id = asset_data[0] # The first item is the main identifier
        search_terms_list = asset_data   # The whole list (kept for potential future use, but not used in mk_query now)

        # Console: Clear separation for assets
        logging.info(f"\n{'='*15} Processing Asset: {primary_asset_id} {'='*15}")
        all_asset_posts = []
        all_asset_rejected = []
        asset_rejection_stats = Counter()

        # Determine sub-directory based on whether the asset_data list is in STOCKS or CRYPTO
        is_stock = any(asset_data == stock_list for stock_list in STOCKS)
        sub_dir = "stocks" if is_stock else "crypto"

        # Use primary_asset_id for file paths
        asset_file_path = os.path.join(OUTPUT_DIR, sub_dir, f"{primary_asset_id}.json")
        rejected_asset_file_path = os.path.join(rejected_dir, f"rejected_{primary_asset_id}.json")

        for month_start in month_ranges(START_DATE, END_DATE):
            # Call fetch_month: Pass asset_id (for query) and search_terms_list (unused by mk_query currently)
            accepted_month, rejected_month, month_stats = fetch_month(
                client, primary_asset_id, search_terms_list, month_start, MONTHLY_TARGET
            )

            # Log the number of accepted posts for this specific asset and month
            logging.info(f"    📈 STATS: {primary_asset_id} - {month_start.strftime('%Y-%m')}: Accepted {len(accepted_month)} posts.")

            all_asset_posts.extend(accepted_month)
            for rej_post in rejected_month:
                rej_post['rejected_for_month'] = month_start.strftime('%Y-%m')
            all_asset_rejected.extend(rejected_month)
            asset_rejection_stats.update(month_stats)

        # Update overall rejection stats after processing all months for an asset
        overall_rejection_stats.update(asset_rejection_stats)

        # Save accepted posts (using primary_asset_id in log)
        try:
            with open(asset_file_path, "w", encoding="utf-8") as f:
                json.dump(all_asset_posts, f, ensure_ascii=False, indent=2)
            logging.info(f"✅ {primary_asset_id}: Saved {len(all_asset_posts)} accepted posts to {asset_file_path}")
        except IOError as e:
            logging.error(f"❌ Error writing accepted file {asset_file_path}: {e}")

        # Save rejected posts for this asset (using primary_asset_id in log)
        try:
            with open(rejected_asset_file_path, "w", encoding="utf-8") as f:
                json.dump(all_asset_rejected, f, ensure_ascii=False, indent=2)
            logging.info(f"ℹ️ {primary_asset_id}: Saved {len(all_asset_rejected)} rejected post details to {rejected_asset_file_path}")
        except IOError as e:
            logging.error(f"❌ Error writing rejected file {rejected_asset_file_path}: {e}")

        # Log asset summary stats (using primary_asset_id)
        logging.info(f"📊 {primary_asset_id}: Total Accepted: {len(all_asset_posts)}")
        logging.info(f"📊 {primary_asset_id}: Total Rejection Stats For This Asset: {dict(asset_rejection_stats)}")

        # Flush the file log handler after processing each asset
        file_handler.flush()
        logging.debug(f"   Log file flushed after processing {primary_asset_id}.")


    logging.info("\n🎉 All assets processed.")
    # Correctly display overall rejection stats aggregated across all assets
    logging.info(f"📊 Overall Rejection Stats Across All Assets: {dict(overall_rejection_stats)}")


if __name__ == "__main__":
    main()