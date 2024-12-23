import logging
import time
from datetime import datetime
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.utils import get_entry_date

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def fetch_entries(
    start_date: datetime.date,
    end_date: datetime.date,
    categories: Iterable[str],
) -> pd.DataFrame:
    # Construct categories query
    categories_with_prefix = ["cat:" + cat for cat in categories]
    categories_concat_str = " OR ".join(categories_with_prefix)

    # Initialise result entries list
    result_entries = []

    # Create date for loop condition
    current_earliest_fetched_date = end_date

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

        # Start the API timer
        start_time = time.time()
        # Make request
        response = requests.get(base_url, params=params, timeout=10)

        # Create soup
        soup = BeautifulSoup(response.text, features="xml")

        # Get all new entries
        new_entries = soup.find_all("entry")

        # Break if no entries were found
        if not new_entries:
            logger.warning(
                "Search chunk returned no entries, "
                "likely due to bad user input or too frequent API requests. "
                "Ending search"
                f"Search parameters: {params}"
            )
            break

        # Append new entries
        result_entries.extend(new_entries)

        # Update earliest fetched date
        current_earliest_fetched_date = min(
            get_entry_date(entry) for entry in new_entries
        )

        # End the timer
        execution_time = time.time() - start_time

        # Calculate the remaining time to 3 seconds
        remaining_time = max(0, 4 - execution_time)

        # Wait for the remaining time (if any)
        time.sleep(remaining_time)

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
