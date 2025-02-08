import logging
import os
import re
import subprocess  # nosec
from datetime import datetime, timedelta
from pathlib import Path

from src.fetch import fetch_entries
from src.filter import add_filter_flags
from src.format import format_entries_as_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class ArxivFilterRun:
    def __init__(self, cfg_dict: dict):
        # Generate run id
        now = datetime.now()
        self.run_id = now.strftime("%Y%m%d%H%M%S") + str(now.microsecond)[:2]

        # Save data from dictionary
        self.cfg_dict = cfg_dict

        self.run_settings = cfg_dict["run settings"]
        self.output_folder_path = self.run_settings["output folder"]
        self.display_by = self.run_settings.get("display by", "filters")

        self.data_dict = cfg_dict["data"]
        self.categories = self.data_dict["categories"]
        self.filters = self.cfg_dict["filters"]

        # Optional arguments
        self.days_to_fetch = self.data_dict.get("days to fetch", 0)
        self.only_new_days = self.data_dict.get("only new days", False)
        self.max_retries = self.run_settings.get("max retries", 3)

        # Format output folder to be absolute
        project_root_folder_path = Path(__file__).resolve().parents[1]
        self.output_folder_path_absolute = (
            project_root_folder_path / self.output_folder_path
        ).resolve()

        # Create folder
        if not os.path.exists(self.output_folder_path_absolute):
            os.makedirs(self.output_folder_path_absolute)

        # Setting future arguments
        self.entries = None
        self.formatted_entries_html = None
        self.output_html_file_name = None
        self.output_html_file_path = None

    def execute(self) -> None:
        # Calculate timeframe
        self.calculate_timeframe()

        # Fetch entries
        logger.info("Fetching all relevant entries")
        self.fetch_entries()

        # Log filter and format
        logger.info("Filtering and formatting entries")

        # Filter entries
        self.filter_entries()

        # Format entries
        self.format_entries()

        # Log save and open
        logger.info("Saving and opening results")

        # Save results
        self.save_results()

        # Open results
        self.open_results()

    def calculate_timeframe(self):
        # Create start and end dates
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=self.days_to_fetch)

        # Check if to run only for new days
        if self.only_new_days:
            # Get all runs
            runs = [
                f
                for f in self.output_folder_path_absolute.iterdir()
                if f.is_file() and f.name.startswith("entries_")
            ]

            # Return if there are no past runs
            if not runs:
                return

            # Get all dates from filenames
            pattern = r"\d{4}-\d{2}-\d{2}_(\d{4}-\d{2}-\d{2})"
            run_end_dates = [re.search(pattern, run.name).group(1) for run in runs]

            # Get max date
            max_end_date = max(
                datetime.strptime(date_str, "%Y-%m-%d").date()
                for date_str in run_end_dates
            )

            # Update start date to max end date
            self.start_date = max_end_date - timedelta(days=1)

    def fetch_entries(self) -> None:
        # Retrieve all entries
        self.entries = fetch_entries(
            self.start_date, self.end_date, self.categories, self.max_retries
        )

    def filter_entries(self) -> None:
        # Get filtered entries
        self.entries = add_filter_flags(self.entries, self.filters)

    def format_entries(self) -> None:
        # Get HTML formatted entries
        self.formatted_entries_html = format_entries_as_html(
            self.entries,
            self.start_date,
            self.end_date,
            self.categories,
            by=self.display_by,
        )

    def save_results(self) -> None:
        # Create html output file path
        self.output_html_file_name = (
            f"entries_"
            f"{self.run_id}__"
            f'{self.start_date.strftime("%Y-%m-%d")}_'
            f'{self.end_date.strftime("%Y-%m-%d")}.html'
        )
        self.output_html_file_path = (
            self.output_folder_path_absolute / self.output_html_file_name
        )

        # Retrieve output file path
        file_path = self.output_html_file_path

        # Save output file
        with open(file_path, "w") as file:
            file.write(self.formatted_entries_html)

    def open_results(self) -> None:
        # Open file
        subprocess.run(["open", self.output_html_file_path])  # nosec
