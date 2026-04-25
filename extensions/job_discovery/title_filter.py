def passes_title_filter(title: str, title_filter: dict) -> bool:
    t = title.lower()
    if not any(kw in t for kw in title_filter.get("positive", [])):
        return False
    if any(kw in t for kw in title_filter.get("negative", [])):
        return False
    return True


def has_seniority_boost(title: str, title_filter: dict) -> bool:
    t = title.lower()
    return any(kw in t for kw in title_filter.get("seniority_boost", []))
