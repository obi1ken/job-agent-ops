import os
from typing import Optional

import requests

from .models import JobListing
from .title_filter import has_seniority_boost, passes_title_filter

_BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
_DEFAULT_SALARY_MIN = 35000
_DEFAULT_LOCATION = "London"   # fallback if ADZUNA_LOCATION not set
_DEFAULT_RADIUS_KM = 50


class AdzunaError(Exception):
    pass


class AdzunaClient:
    def __init__(self):
        self._app_id = os.environ["ADZUNA_APP_ID"]
        self._app_key = os.environ["ADZUNA_API_KEY"]
        self._location = os.environ.get("ADZUNA_LOCATION", _DEFAULT_LOCATION)
        self._radius = int(os.environ.get("ADZUNA_LOCATION_RADIUS", str(_DEFAULT_RADIUS_KM)))
        self._salary_min = int(os.environ.get("ADZUNA_SALARY_MIN", str(_DEFAULT_SALARY_MIN)))

    def fetch(self, query: str, title_filter: dict, results_per_page: int = 50) -> list[JobListing]:
        params = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "what": query,
            "where": self._location,
            "distance": self._radius,
            "salary_min": self._salary_min,
            "full_time": 1,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise AdzunaError(f"Adzuna API request failed: {exc}") from exc
        except ValueError as exc:
            raise AdzunaError(f"Adzuna response not valid JSON: {exc}") from exc

        listings = []
        for item in data.get("results", []):
            listing = self._parse_result(item, title_filter)
            if listing is not None:
                listings.append(listing)
        return listings

    def _parse_result(self, item: dict, title_filter: dict) -> Optional[JobListing]:
        title = item.get("title", "")
        if not passes_title_filter(title, title_filter):
            return None
        return JobListing(
            source="adzuna",
            external_id=str(item.get("id", "")),
            title=title,
            company=item.get("company", {}).get("display_name", ""),
            location=item.get("location", {}).get("display_name", ""),
            description=item.get("description", "")[:500],
            url=item.get("redirect_url", ""),
            salary_min=_to_int(item.get("salary_min")),
            salary_max=_to_int(item.get("salary_max")),
            posted_date=item.get("created", ""),
            seniority_boost=has_seniority_boost(title, title_filter),
            raw=item,
        )


def _to_int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None
