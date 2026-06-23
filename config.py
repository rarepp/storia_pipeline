# config.py

KNOWN_NEIGHBORHOODS = [
    "copou", "tatarasi", "nicolina", "cantemir", "pacurari", "cug", "bularga",
    "bucium", "centru", "podu ros", "dacia", "mircea", "galata", "alexandru",
    "tudor", "frumoasa", "manta rosie", "gara", "sararie", "socola"
]


def resolve_exact_neighborhood(title, slug, extracted_val):
    search_zone = f"{title} {slug}".lower()

    # Standardize variations of Valea Lupului
    if "v luplui" in search_zone or "v lupului" in search_zone or "valea lupului" in search_zone:
        return "Valea Lupului"

    clean_val = str(extracted_val).strip()
    if clean_val in ["Iași", "Necunoscut", "", "None"]:
        for zone in KNOWN_NEIGHBORHOODS:
            if zone in search_zone:
                return zone.title()
        return "Iași Central / General"
    return clean_val