"""Normalized lead, contact, and search-criteria models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

LeadType = Literal["client", "freelance", "contract", "full_time", "all"]
IntentClass = Literal["EXPLICIT_DEMAND", "STRONG_SIGNAL", "POTENTIAL_FIT"]
Workplace = Literal["remote", "hybrid", "onsite", "unknown"]
DiscoveryMode = Literal["jobs", "radar", "agency"]
OpportunityEventType = Literal[
    "funding",
    "saas_launch",
    "agency_client_win",
    "eng_team_expansion",
    "tech_hiring",
    "none",
]
PartnershipFit = Literal[
    "white_label",
    "overflow_capacity",
    "design_only_gap",
    "consultancy_contract",
    "none",
]
ContactPathRole = Literal[
    "founder",
    "engineering_manager",
    "recruiter",
    "hiring_contact",
    "application_form",
    "unknown",
]
LeadStatus = Literal[
    "new",
    "qualified",
    "shortlisted",
    "contacted",
    "replied",
    "meeting",
    "proposal",
    "won",
    "lost",
    "disqualified",
    "expired",
    "needs_review",
]
ContactVerification = Literal[
    "published_on_official_source",
    "domain_mx_present",
    "unverified",
    "unknown",
    "not_applicable",
]


@dataclass
class SearchCriteria:
    lead_types: list[LeadType] = field(default_factory=lambda: ["all"])
    technologies: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    geographies: list[str] = field(default_factory=list)
    workplace: list[Workplace] = field(default_factory=lambda: ["remote", "hybrid", "onsite"])
    budget_or_salary: Optional[str] = None
    limit: int = 20
    freshness_days: int = 30
    require_sponsorship: bool = False
    require_relocation: bool = False
    excluded_sources: list[str] = field(default_factory=list)
    excluded_companies: list[str] = field(default_factory=list)
    excluded_lead_ids: list[str] = field(default_factory=list)
    discovery_modes: list[DiscoveryMode] = field(default_factory=lambda: ["jobs"])
    query_text: str = ""
    raw_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContactChannel:
    channel_type: Literal[
        "email",
        "contact_form",
        "application_page",
        "professional_profile",
        "hiring_post",
        "unknown",
    ]
    value: str = ""
    name: Optional[str] = None
    title: Optional[str] = None
    source_url: str = ""
    verification_status: ContactVerification = "unknown"
    verification_method: str = ""
    date_checked: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Evidence:
    summary: str
    excerpt: str = ""
    source_url: str = ""
    published_date: Optional[str] = None
    checked_date: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OutreachDraft:
    subject: str = ""
    email_body: str = ""
    networking_message: str = ""
    service_proposal: str = ""
    call_to_action: str = ""
    personalization_facts: list[str] = field(default_factory=list)
    application_message: str = ""
    recruiter_outreach: str = ""
    partnership_pitch: str = ""
    send_approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OpportunityEvent:
    event_type: OpportunityEventType = "none"
    summary: str = ""
    corroborating_signals: list[str] = field(default_factory=list)
    demand_proven: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgencyPartnership:
    is_agency: bool = False
    partnership_fit: PartnershipFit = "none"
    pitch_angle: str = ""
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreferredContactPath:
    role: ContactPathRole = "unknown"
    channel_type: str = ""
    value: str = ""
    name: Optional[str] = None
    title: Optional[str] = None
    source_url: str = ""
    relevance: str = ""
    avoid_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LeadScores:
    intent_score: float
    fit_score: float
    contact_score: float
    freshness_score: float
    overall: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["intent_score"] = round(self.intent_score, 3)
        d["fit_score"] = round(self.fit_score, 3)
        d["contact_score"] = round(self.contact_score, 3)
        d["freshness_score"] = round(self.freshness_score, 3)
        d["overall"] = round(self.overall, 3)
        return d


@dataclass
class Lead:
    id: str
    name: str
    lead_type: LeadType
    company: str
    title: str
    url: str
    source: str
    intent: IntentClass
    intent_explanation: str
    evidence: list[Evidence] = field(default_factory=list)
    technical_requirements: list[str] = field(default_factory=list)
    profile_match_reasons: list[str] = field(default_factory=list)
    recommended_service: str = ""
    contacts: list[ContactChannel] = field(default_factory=list)
    budget_or_salary: Optional[str] = None
    location: str = ""
    workplace: Workplace = "unknown"
    country: Optional[str] = None
    published_date: Optional[str] = None
    checked_date: Optional[str] = None
    status: LeadStatus = "new"
    expired: bool = False
    risks: list[str] = field(default_factory=list)
    next_action: str = ""
    scores: Optional[LeadScores] = None
    outreach: Optional[OutreachDraft] = None
    confidence: Optional[float] = None
    review_reason: str = ""
    content_hash: str = ""
    opportunity: Optional[OpportunityEvent] = None
    partnership: Optional[AgencyPartnership] = None
    preferred_contact: Optional[PreferredContactPath] = None
    last_contact_date: Optional[str] = None
    next_followup_date: Optional[str] = None
    notes: str = ""
    outcome: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.scores is not None:
            d["scores"] = self.scores.to_dict()
        if self.outreach is not None:
            d["outreach"] = self.outreach.to_dict()
        if self.opportunity is not None:
            d["opportunity"] = self.opportunity.to_dict()
        if self.partnership is not None:
            d["partnership"] = self.partnership.to_dict()
        if self.preferred_contact is not None:
            d["preferred_contact"] = self.preferred_contact.to_dict()
        d["evidence"] = [e.to_dict() for e in self.evidence]
        d["contacts"] = [c.to_dict() for c in self.contacts]
        return d
