from datetime import datetime


def get_entry_date(entry):
    return datetime.strptime(entry.updated.text, "%Y-%m-%dT%H:%M:%SZ").date()


def get_entry_id_string(entry):
    return entry.id.text.split("/")[-1]


def get_entry_url(entry):
    return entry.id.text.strip("\n")


def get_entry_authors_string(entry):
    # Extract all authors
    authors_list = entry.find_all("author")

    # Extract texts from soups
    authors_list_strings = [x.text.strip(" \n") for x in authors_list]

    # Concatenate strings
    authors_string = ", ".join(authors_list_strings)

    return authors_string
