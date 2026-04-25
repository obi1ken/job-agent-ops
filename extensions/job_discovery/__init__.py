import logging
import os

from .models import JobListing
from .runner import JobDiscovery, JobDiscoveryError

__all__ = ["JobDiscovery", "JobDiscoveryError", "JobListing"]


def run_discovery() -> None:
    discovery = JobDiscovery(
        portals_yml_path=os.environ.get("PORTALS_YML_PATH", "portals.yml"),
        state_path=os.environ.get(
            "DISCOVERY_STATE_PATH",
            "extensions/job_discovery/discovery_state.json",
        ),
    )
    listings = discovery.run()
    log = logging.getLogger(__name__)
    for listing in listings:
        boost = " [SENIOR]" if listing.seniority_boost else ""
        log.info("[%s]%s %s @ %s — %s", listing.source.upper(), boost, listing.title, listing.company, listing.url[:60])
