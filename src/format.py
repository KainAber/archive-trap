from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from yattag import Doc

from src.utils import get_entry_authors_string, get_entry_url


def format_entries_as_html(
    entries: pd.DataFrame,
    start_date: datetime.date,
    end_date: datetime.date,
    categories: Iterable[str],
    by="entries",
) -> str:

    # Generate HTML content using yattag
    doc, tag, text = Doc().tagtext()

    # Construct HTML
    with tag("html"):
        with tag("head"):
            doc.stag("meta", charset="UTF-8")
            add_js_to_html(doc, tag, text)
            add_css_to_html(doc, tag, text)
            with tag("title"):
                text("arXiv Results")
        with tag("body"):
            with tag("div", klass="headerbox"):
                with tag("div", klass="header"):
                    text("arXiv Results")
                with tag("div", klass="subheader"):
                    text(
                        ", ".join(categories)
                        + ": "
                        + start_date.strftime("%d.%m.%Y")
                        + " - "
                        + end_date.strftime("%d.%m.%Y")
                    )
            with tag("div", klass="text"):
                # Display by entries
                if by == "entries":
                    # Add entries by filters
                    add_entries_to_html_by_entries(doc, tag, text, entries)
                # Display by filters
                elif by == "filters":
                    # Add entries by filters
                    add_entries_to_html_by_filters(doc, tag, text, entries)
                # The display type is not supported
                else:
                    raise ValueError(f"The display type {by} is not supported")

    # Convert HTML to string
    html_content = doc.getvalue()

    return html_content


def add_entries_to_html_by_entries(doc, tag, text, entries: pd.DataFrame) -> None:
    # Remove entries without a filter trigger
    entries_filtered = entries[entries.any(axis=1)]

    # Go through entries
    for entry, row in entries_filtered.iterrows():
        # Extract triggered filters
        filters = [f for f in row.index if row[f]]

        # Format filters
        filters_strings = [f"{f[0]}: {f[1]}" for f in filters]

        # Add entry to html
        add_entry_to_html(doc, tag, text, entry, filters_strings)


def add_entries_to_html_by_filters(doc, tag, text, entries: pd.DataFrame) -> None:
    # Group by the filter
    for filter_name, sub_df in entries.T.groupby(level=0, sort=False):
        # Add flag for entry added
        entry_added = False

        # Write filter
        with tag("h2"):
            text(f"{filter_name}\n")

        # Re-transpose the dataframe
        sub_df = sub_df.T

        # Go through each entry
        for i in range(len(sub_df)):
            # Get the entry
            entry = sub_df.index[i]

            # Get the entry row
            entry_row = sub_df.iloc[i]

            # Get only the keywords which were found
            entry_row = entry_row[entry_row]

            # Check if keywords were found
            if not entry_row.empty:
                # Extract all keywords
                keywords_strings = entry_row.index.get_level_values(1)

                # Add entry to html
                add_entry_to_html(doc, tag, text, entry, keywords_strings)

                # Update flag
                entry_added = True

        # Add text for no entry
        if not entry_added:
            with tag("div", klass="italicolor"):
                text("No new entries\n")


def add_entry_to_html(doc, tag, text, entry, keywords) -> None:
    with tag("div", klass="latex-content"):
        with tag("h3"):
            with tag("a", href=get_entry_url(entry), target="_blank"):
                text(f"{entry.title.text}")
    with tag("p"):
        text(f"{get_entry_authors_string(entry)}")

    with tag("p"):
        with tag("strong"):
            text("Abstract:")
    with tag("div", klass="latex-content"):
        with tag("p"):
            doc.asis(entry.summary.text)
    with tag("p"):
        with tag("strong"):
            text("Keywords: ")
        with tag("em"):
            text(", ".join(keywords))


def add_js_to_html(doc, tag, text) -> None:
    with tag("script", type="text/javascript"):
        doc.asis(
            """
        MathJax = {
            tex: {
                inlineMath: [['$', '$']]
            }
        };
        """
        )
    with tag(
        "script",
        src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js",
    ):
        pass


def add_css_to_html(doc, tag, text) -> None:
    with tag("style"):
        with open(Path(__file__).parent / "theme.css", "r") as file:
            theme_css = file.read()
        text(theme_css)
