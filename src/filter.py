from typing import Any, Iterable

import pandas as pd


def add_filter_flags(
    entries_df: pd.DataFrame, filters: list[dict[str, Any]]
) -> pd.DataFrame:

    # Define column hierarchy
    multi_index_columns = pd.MultiIndex.from_tuples([], names=["Filter", "Keyword"])

    # Add column hierarchy
    entries_df.columns = multi_index_columns

    # Go through all filters
    for filter in filters:

        # Add single filter flag
        add_filter_flag(entries_df, filter)

    return entries_df


def add_filter_flag(entries_df: pd.DataFrame, filter: dict[str, Any]):
    filter_name = filter["name"]
    filter_fields = filter["fields"]
    filter_keywords = filter["keywords"]

    for keyword in filter_keywords:
        entries_df[(filter_name, keyword)] = entries_df.index.to_series().apply(
            lambda x: contains_keyword_in_fields(x, filter_fields, keyword)
        )


def contains_keyword_in_fields(entry, fields: Iterable[str], keyword: str) -> bool:
    # Compare keyword against all fields
    contains = any(contains_keyword_in_field(entry, field, keyword) for field in fields)

    return contains


def contains_keyword_in_field(entry, field_name, keyword) -> bool:
    # Get all values from entry
    field_values = [x.text for x in entry.find_all(field_name)]

    # Clean strings for comparison
    field_values_clean = [value.lower().strip(" \n") for value in field_values]
    keyword_clean = keyword.lower()

    # Compare if keyword_lower can be found as substring
    contains = any(keyword_clean in x for x in field_values_clean)

    return contains
