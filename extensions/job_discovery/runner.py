import logging
import os

from .adzuna_client import AdzunaClient, AdzunaError
from .config_loader import ConfigError, get_enabled_queries, get_title_filter, load_portals_config
from .discovery_state import DiscoveryState
from .models import JobListing
from .serpapi_client import SerpApiClient, SerpApiError

log = logging.getLogger(__name__)

_DEFAULT_STATE_PATH = "extensions/job_discovery/discovery_state.json"
_DEFAULT_MAX_NEW_PER_TICK = 3


class JobDiscoveryError(Exception):
    pass


def _rotate(queries: list[dict], offset: int) -> list[dict]:
    if not queries:
        return queries
    k = offset % len(queries)
    return queries[k:] + queries[:k]


def _filter_job_type(queries: list[dict], job_type: str) -> list[dict]:
    """Keep only queries for one job type (matched by 'Track X' in the query
    name). Empty job_type = no filtering."""
    if not job_type:
        return queries
    needle = f"track {job_type.lower()}"
    return [q for q in queries if needle in q.get("name", "").lower()]


class JobDiscovery:
    def __init__(self, portals_yml_path: str, state_path: str = _DEFAULT_STATE_PATH):
        try:
            self._config = load_portals_config(portals_yml_path)
        except ConfigError as exc:
            raise JobDiscoveryError(str(exc)) from exc
        self._title_filter = get_title_filter(self._config)
        self._state = DiscoveryState(
            os.environ.get("DISCOVERY_STATE_PATH", state_path)
        )

    def run(self) -> list[JobListing]:
        all_listings: list[JobListing] = []
        max_new = int(
            os.environ.get("MAX_NEW_JOBS_PER_TICK", _DEFAULT_MAX_NEW_PER_TICK)
        )
        # Rotate the starting query each tick so the per-tick cap doesn't
        # starve later tracks (queries are ordered Track A→D in portals.yml).
        offset = self._state.bump_rotation()

        # Targeted search: DISCOVERY_JOB_TYPE=A|B|C|D limits this fetch to one
        # job type's queries (Charles: "search document control" → D).
        job_type = os.environ.get("DISCOVERY_JOB_TYPE", "").strip().upper()

        # Adzuna
        adzuna_queries = _rotate(
            _filter_job_type(get_enabled_queries(self._config, "adzuna"), job_type),
            offset,
        )
        if adzuna_queries and len(all_listings) < max_new:
            try:
                client = AdzunaClient()
                all_listings.extend(
                    self._run_source(
                        "adzuna", client, adzuna_queries, max_new - len(all_listings)
                    )
                )
            except (KeyError, AdzunaError) as exc:
                log.error("Adzuna source failed: %s", exc)

        # SerpAPI
        serpapi_queries = _rotate(
            _filter_job_type(get_enabled_queries(self._config, "serpapi"), job_type),
            offset,
        )
        if serpapi_queries and len(all_listings) < max_new:
            try:
                client = SerpApiClient()
                all_listings.extend(
                    self._run_source(
                        "serpapi", client, serpapi_queries, max_new - len(all_listings)
                    )
                )
            except (KeyError, SerpApiError) as exc:
                log.error("SerpAPI source failed: %s", exc)

        self._state.prune()
        self._state.save()
        log.info(
            "job_discovery: %d new listings found (cap %d per tick)",
            len(all_listings),
            max_new,
        )
        return all_listings

    def _run_source(
        self, source: str, client, queries: list[dict], budget: int
    ) -> list[JobListing]:
        new_listings: list[JobListing] = []
        for query_cfg in queries:
            query = query_cfg.get("query", "")
            log.debug("Fetching %s: %s", source, query_cfg.get("name", query[:40]))
            try:
                results = client.fetch(query, self._title_filter)
            except (AdzunaError, SerpApiError) as exc:
                log.error("Query '%s' failed: %s", query_cfg.get("name", ""), exc)
                continue
            for listing in results:
                if len(new_listings) >= budget:
                    # Unprocessed listings stay unseen — picked up next tick
                    log.info(
                        "%s: per-tick cap reached, deferring remaining listings",
                        source,
                    )
                    return new_listings
                if self._state.is_seen(source, listing.external_id):
                    continue
                self._state.mark_seen(source, listing.external_id)
                new_listings.append(listing)
        return new_listings
