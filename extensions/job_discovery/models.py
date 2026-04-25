from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobListing:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    posted_date: Optional[str] = None
    seniority_boost: bool = False
    raw: dict = field(default_factory=dict)
