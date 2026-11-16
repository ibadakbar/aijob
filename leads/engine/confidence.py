"""Confidence gate: qualify clear demand, and hold everything else for review."""

from __future__ import annotations

from .model import Lead

DEFAULT_QUALIFY_THRESHOLD = 0.72


def confidence_of(lead: Lead) -> tuple[float, list[str]]:
    """Explainable 0–1 confidence. This is not a model score from a paid API."""
    reasons: list[str] = []
    if lead.intent == "EXPLICIT_DEMAND":
        score = 0.62
        reasons.append("explicit public demand")
    elif lead.intent == "STRONG_SIGNAL":
        score = 0.40
        reasons.append("supporting signal without an explicit request")
    else:
        score = 0.22
        reasons.append("no established demand")

    if any((e.source_url or lead.url) and (e.excerpt or e.summary) for e in lead.evidence):
        score += 0.14
        reasons.append("source URL and excerpt are stored")
    else:
        score -= 0.10
        reasons.append("auditable evidence is missing")

    if lead.published_date:
        score += 0.05
        reasons.append("published date present")

    if lead.scores is not None and lead.scores.fit_score >= 0.45:
        score += 0.08
        reasons.append("profile fit supports the listing")

    if any(c.verification_status == "published_on_official_source" and c.value for c in lead.contacts):
        score += 0.06
        reasons.append("contact channel was published on the source")

    if lead.expired:
        score -= 0.25
        reasons.append("listing is expired")

    if lead.opportunity and lead.opportunity.event_type != "none":
        if lead.opportunity.demand_proven:
            score = min(1.0, score + 0.05)
            reasons.append("opportunity event corroborated by demand evidence")
        else:
            score = min(score, 0.55)
            reasons.append("opportunity event without proven demand (not a lead yet)")

    return max(0.0, min(1.0, score)), reasons


def decide_status(
    lead: Lead,
    confidence: float,
    *,
    threshold: float = DEFAULT_QUALIFY_THRESHOLD,
) -> tuple[str, str]:
    """Auto-qualify only explicit, current demand above the threshold."""
    if lead.expired:
        return "needs_review", "Expired listing stays in the review queue."
    has_evidence = any((e.source_url or lead.url) and (e.excerpt or e.summary) for e in lead.evidence)
    if lead.opportunity and lead.opportunity.event_type != "none" and not lead.opportunity.demand_proven:
        return (
            "needs_review",
            "Opportunity radar found an event without corroborating demand — not auto-qualified.",
        )
    if lead.intent != "EXPLICIT_DEMAND":
        return (
            "needs_review",
            f"Intent {lead.intent} is not explicit demand, so it is not auto-qualified.",
        )
    if not has_evidence:
        return "needs_review", "Missing source URL or excerpt, so it is not auto-qualified."
    if confidence < threshold:
        return "needs_review", f"Confidence {confidence:.2f} is below {threshold:.2f}."
    return (
        "qualified",
        "Explicit demand with auditable evidence above the confidence threshold.",
    )
