import re
import warnings

from .models import EDMSResult

# word-boundary scan needed for short tokens to avoid false positives
_WHOLE_WORD_TOKENS = {"acc"}

EDMS_PLATFORMS: dict[str, list[str]] = {
    "Aconex":       ["aconex", "oracle aconex"],
    "Asite":        ["asite", "a-site"],
    "Procore":      ["procore"],
    "Viewpoint":    ["viewpoint", "viewpoint for projects", "4projects"],
    "Dalux":        ["dalux"],
    "SharePoint":   ["sharepoint"],
    "BIM 360 / ACC": ["bim 360", "autodesk construction cloud", "acc"],
}


class EDMSNotDetectedWarning(UserWarning):
    """Issued when Track D is selected but no EDMS platform is found in the JD.
    Orchestrator must run a web search for the company's EDMS before generating
    the cover letter."""


class EDMSDetector:
    def detect(self, jd_text: str) -> EDMSResult:
        text = jd_text.lower()
        platforms_found: list[str] = []
        raw_matches: dict[str, list[str]] = {}

        for platform, keywords in EDMS_PLATFORMS.items():
            matched = []
            for kw in keywords:
                pattern = rf"\b{re.escape(kw)}\b" if kw in _WHOLE_WORD_TOKENS else re.escape(kw)
                if re.search(pattern, text):
                    matched.append(kw)
            if matched:
                platforms_found.append(platform)
                raw_matches[platform] = matched

        return EDMSResult(platforms_found=platforms_found, raw_matches=raw_matches)

    def detect_for_track_d(self, jd_text: str, company: str, role: str) -> EDMSResult:
        result = self.detect(jd_text)
        if not result.platforms_found:
            warnings.warn(
                f"No EDMS platform detected in JD for {company!r} — {role!r}. "
                "Orchestrator must run web search before generating Track D cover letter.",
                EDMSNotDetectedWarning,
                stacklevel=2,
            )
        return result
