from .models import PrepInput, ResearchTargets

_TRACK_QUERIES: dict[str, str] = {
    "A": "{company} AI infrastructure machine learning engineering stack",
    "B": "{company} product roadmap AI strategy digital transformation",
    "C": "{company} infrastructure projects Network Rail contracts digital railway",
    "D": "{company} document control EDMS platform Aconex Asite Procore Viewpoint",
}


def build_research_targets(prep_input: PrepInput) -> ResearchTargets:
    company = prep_input.company
    role = prep_input.role
    track = prep_input.track.upper()

    queries = [
        f"{company} latest news 2025 2026",
        f"{company} products services overview",
        f"{company} interview process format experience",
        f'"{role}" {company} responsibilities salary UK',
        f"{company} engineering culture values team",
    ]

    track_query = _TRACK_QUERIES.get(track, "")
    if track_query:
        queries.append(track_query.format(company=company))

    return ResearchTargets(queries=queries)
