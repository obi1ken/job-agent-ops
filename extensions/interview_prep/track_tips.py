_TIPS: dict[str, str] = {
    "A": """Track A — Engineering focus.
Lead with MT5 Portfolio Risk Governor (7-check system) and Lobi Eco 6-agent isolation design.
Highlight Claude Code depth, Python 3.11, autonomous agent architecture, phase boundary enforcement.
Ask questions probing their tech stack, deployment infrastructure, and agent orchestration challenges.
For Likely Questions: expect system design, failure handling, multi-agent coordination, production reliability.""",

    "B": """Track B — Product & Leadership focus.
Lead with Quintech (BAT/P&G/Nokia delivery) and Tavistock NHS digital transformation.
Highlight 20 years senior stakeholder management and end-to-end product ownership.
Ask about AI adoption roadmap, product strategy, team structure, and success metrics.
For Likely Questions: expect PM process, prioritisation frameworks, stakeholder conflict, AI product metrics.""",

    "C": """Track C — Rail/Civils Digital focus.
Lead with COSS/PC operational credentials — this is the rare differentiator in this market.
Reference Rule Book (GERT8000-HB7/HB8), Sentinel, multi-group line blockage experience.
Ask about specific infrastructure programme, NR standards compliance, ERTMS timeline.
For Likely Questions: expect COSS/PC scenario questions, NR standards knowledge, digital signalling context.""",

    "D": """Track D — Document Control focus.
Lead with Consepsys certification and Tavistock NHS archive project as primary evidence.
Reference the specific EDMS platform the company uses if detected from the JD.
Ask about metadata schema, transmittal process, and ISO 19650 implementation maturity.
For Likely Questions: expect EDMS platform knowledge, version control procedures, audit trail requirements.""",
}


def get_track_tips(track: str) -> str:
    return _TIPS.get(track.upper(), _TIPS["A"])
