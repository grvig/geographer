"""Whether a matched clue fits where the image was taken.

This runs after matching and never changes the match: a clue from elsewhere is
shown as a look-alike instead.
"""


def is_consistent(clue: dict, country: str | None, admin1: str | None) -> bool:
    for region in clue["regions"]:
        if region["country"] != country:
            continue
        # A region naming a state or province covers only that one.
        if "admin1" not in region or region["admin1"] == admin1:
            return True
    return False
