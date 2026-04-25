import hashlib
import os
from typing import Optional

import requests

from .models import JobListing
from .title_filter import has_seniority_boost, passes_title_filter

_BASE_URL = "https://serpapi.com/search"


class SerpApiError(Exception):
    pass


class SerpApiClient:
    def __init__(self):
        self._api_key = os.environ["SERPAPI_KEY"]

    def fetch(self, query: str, title_filter: dict, location: str = "United Kingdom") -> list[JobListing]:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "api_key": self._api_key,
        }
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise SerpApiError(f"SerpAPI request failed: {exc}") from exc
        except ValueError as exc:
            raise SerpApiError(f"SerpAPI response not valid JSON: {exc}") from exc

        listings = []
        for item in data.get("jobs_results", []):
            listing = self._parse_result(item, title_filter)
            if listing is not None:
                listings.append(listing)
        return listings

    def _parse_result(self, item: dict, title_filter: dict) -> Optional[JobListing]:
        title = item.get("title", "")
        if not passes_title_filter(title, title_filter):
            return None

        apply_options = item.get("apply_options", [])
        url = apply_options[0].get("link", "") if apply_options else ""
        external_id = _stable_id(url or f"{title}{item.get('company_name', '')}{item.get('detected_extensions', {}).get('posted_at', '')}")

        return JobListing(
            source="serpapi",
            external_id=external_id,
            title=title,
            company=item.get("company_name", ""),
            location=item.get("location", ""),
            description=item.get("description", "")[:500],
            url=url,
            salary_min=None,
            salary_max=None,
            posted_date=item.get("detected_extensions", {}).get("posted_at", ""),
            seniority_boost=has_seniority_boost(title, title_filter),
            raw=item,
        )


def _stable_id(seed: str) -> str:
    return "serpapi:" + hashlib.sha256(seed.encode()).hexdigest()[:16]
