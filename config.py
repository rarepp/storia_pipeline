# config.py

KNOWN_NEIGHBORHOODS = [
    "copou", "tatarasi", "nicolina", "cantemir", "pacurari", "cug", "bularga",
    "bucium", "centru", "podu ros", "dacia", "mircea", "galata", "alexandru",
    "tudor", "frumoasa", "manta rosie", "gara", "sararie", "socola",
    "podul de piatra", "moara de foc", "valea lupului", "ciurchi", "meteo"
]


def resolve_exact_neighborhood(title, slug, raw_labels_list):
    """
    Highly resilient neighborhood mapping parser that cross-references
    JSON structural labels and fallback regex title strings.
    """
    search_strings = []

    # 1. Inspect the structural location JSON markers
    if raw_labels_list and isinstance(raw_labels_list, list):
        for entry in raw_labels_list:
            if isinstance(entry, dict) and "label" in entry:
                label_val = str(entry.get("label", "")).strip()
                label_lower = label_val.lower()

                # Instantly isolate high-confidence targets from backend tags
                if entry.get("type") in ["DISTRICT", "QUARTER", "SUB_DISTRICT"]:
                    if label_lower not in ["iași", "iasi", "necunoscut", ""]:
                        if "valea lupului" in label_lower: return "Valea Lupului"
                        if "podu" in label_lower and "piatra" in label_lower: return "Podul de Piatră"
                        if "moara" in label_lower and "foc" in label_lower: return "Moara de Foc"
                        return label_val

                # Collect other labels for fallback processing
                if label_lower not in ["românia", "romania", "iași", "iasi"]:
                    search_strings.append(label_lower)

    # 2. Add title and slug strings into the lookup pool
    search_strings.append(str(title).lower())
    search_strings.append(str(slug).lower())

    # Standardize our unified search target context
    unified_search_context = " ".join(search_strings)

    # 3. Apply manual override parsing blocks for compound names
    if "v luplui" in unified_search_context or "v lupului" in unified_search_context or "valea lupului" in unified_search_context:
        return "Valea Lupului"
    if "podu" in unified_search_context and "piatra" in unified_search_context:
        return "Podul de Piatră"
    if "moara" in unified_search_context and "foc" in unified_search_context:
        return "Moara de Foc"
    if "podu" in unified_search_context and "ros" in unified_search_context:
        return "Podu Roș"
    if "manta" in unified_search_context and "rosie" in unified_search_context:
        return "Manta Roșie"

    # 4. Check keyword intersections
    for zone in KNOWN_NEIGHBORHOODS:
        if zone in unified_search_context:
            if zone == "podul de piatra": return "Podul de Piatră"
            if zone == "moara de foc": return "Moara de Foc"
            if zone == "podu ros": return "Podu Roș"
            if zone == "manta rosie": return "Manta Roșie"
            return zone.title()

    return "Iași Central / General"