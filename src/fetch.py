import logging
import time
from datetime import datetime
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.utils import get_entry_date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def fetch_entries(
    start_date: datetime.date,
    end_date: datetime.date,
    categories: Iterable[str],
    max_retries,
) -> pd.DataFrame:
    # Construct categories query
    categories_with_prefix = ["cat:" + cat for cat in categories]
    categories_concat_str = " OR ".join(categories_with_prefix)

    # Initialise result entries list
    result_entries = []

    # Calculate number of days needed
    num_days_to_fetch = (end_date - start_date).days

    # Create date for loop condition
    current_earliest_fetched_date = end_date

    # Create available retries to count down
    available_retries = max_retries

    # Create success flag for progress bar finalsiation
    successful_fetch = True

    # Log fetching
    with tqdm(
        total=num_days_to_fetch,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} {postfix}",
    ) as pbar:
        # Set description
        pbar.set_description("Fetching days")

        # Fetch entries while we have not reached beyond the earliest date
        while start_date <= current_earliest_fetched_date:

            # Define base URL
            base_url = "http://export.arxiv.org/api/query"

            # Define search parameters
            params = {
                "search_query": categories_concat_str,
                "start": len(result_entries),
                "max_results": 200,
                "sortBy": "lastUpdatedDate",
                "sortOrder": "descending",
            }

            # Make request
            response = requests.get(base_url, params=params, timeout=10)

            # Create soup
            soup = BeautifulSoup(response.text, features="xml")

            # Get all new entries
            new_entries = soup.find_all("entry")

            # Retry if there are retries available
            if not new_entries and available_retries > 0:
                # Reduce available retries
                available_retries -= 1

                # Retries open
                next_retry = max_retries - available_retries

                # Update description progress bar
                pbar.set_postfix({"Retries": f"{next_retry}/{max_retries}"})

                # Wait for the API to recover (increase time for each try)
                time.sleep(3 * next_retry)

                # Retry
                continue

            if not new_entries and not available_retries > 0:
                # Warn the user about the results
                logger.warning(
                    "Ending search due to empty API response, "
                    "likely due to bad user input or too frequent API requests. "
                    f"Search parameters: {params}"
                )

                # Update success flag for progress bar
                successful_fetch = False

                # Break out of the loop
                break

            # Append new entries
            result_entries.extend(new_entries)

            # Update earliest fetched date
            current_earliest_fetched_date_new = min(
                get_entry_date(entry) for entry in new_entries
            )

            # Calculate number of days fetched
            new_days = (
                current_earliest_fetched_date - current_earliest_fetched_date_new
            ).days + 1

            # Update progress bar
            pbar.update(min(new_days, pbar.total - pbar.n - 1))

            # Reset progress bar comment
            pbar.set_postfix("")

            # Update loop conditional
            current_earliest_fetched_date = current_earliest_fetched_date_new

            # Reset the first try flag
            available_retries = max_retries

        # Update progress bar
        if successful_fetch:
            pbar.update(1)

    # Filter out entries from before the earliest day
    result_entries_in_timeframe = [
        entry for entry in result_entries if start_date <= get_entry_date(entry)
    ]

    # Transform dict into dataframe
    results_entries_df = pd.DataFrame(index=result_entries_in_timeframe)

    return results_entries_df


if __name__ == "__main__":
    entries_fetched = fetch_entries(7, ["math.RT", "math.CO"])
    print(entries_fetched.shape)
