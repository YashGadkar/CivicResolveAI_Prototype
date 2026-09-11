import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .config import get_settings
from .core_routes import get_current_user
from .database import get_db
from .models import User
from .schemas import AnalyzeComplaintRequest, ComplaintAnalysis, ComplaintBatchAnalysis, LocationVerificationResponse
from .services.location import verify_location
from .services.pipeline import CATEGORY_RULES, analyze_complaint, classify, detect_language
from .services.ticketing import find_duplicates

settings = get_settings()
router = APIRouter(prefix=settings.api_prefix, tags=["Complaint intelligence"])

# These separators are only accepted when the resulting chunks contain at least
# two distinct civic-service categories. That prevents normal commas in places
# such as "Akurdi, Pune" from creating false tickets.
_CANDIDATE_SEPARATOR_RE = re.compile(
    r"(?:\n+|;|\s*,\s*|(?<=[.!?।])\s+|\s+(?:and|and also|also|plus|along with|as well as|furthermore|moreover|"
    r"आणि|तसेच|और|साथ ही|এবং|અને|மற்றும்|మరియు|ಮತ್ತು|കൂടാതെ|اور)\s+)",
    re.IGNORECASE,
)
_SHARED_RISK_TERMS = (
    "safety risk",
    "public health risk",
    "health risk",
    "serious hazard",
    "immediate intervention",
    "danger to residents",
    "risk to residents",
)


def _category(text: str) -> str:
    return classify(text)[0]


def _merge_generic_context(parts: list[str]) -> list[str]:
    """Attach preambles/trailing context to a nearby recognized civic issue."""
    labels = [_category(part) for part in parts]
    known_positions = [index for index, label in enumerate(labels) if label != "Other Civic Service"]
    if len({labels[index] for index in known_positions}) < 2:
        return []

    merged: list[tuple[str, str]] = []
    pending_prefix: list[str] = []
    for index, part in enumerate(parts):
        label = labels[index]
        if label == "Other Civic Service":
            if merged:
                previous_label, previous_text = merged[-1]
                merged[-1] = (previous_label, f"{previous_text} {part}".strip())
            else:
                pending_prefix.append(part)
            continue

        text = " ".join([*pending_prefix, part]).strip() if pending_prefix else part
        pending_prefix.clear()
        if merged and merged[-1][0] == label:
            merged[-1] = (label, f"{merged[-1][1]} {text}".strip())
        else:
            merged.append((label, text))

    if pending_prefix and merged:
        label, value = merged[-1]
        merged[-1] = (label, f"{value} {' '.join(pending_prefix)}".strip())

    return [value for _, value in merged]


def split_civic_issues(text: str) -> list[str]:
    """Split one citizen message into distinct service problems without over-splitting addresses."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    # First try broad punctuation/conjunction segmentation. We only keep it when
    # multiple distinct recognized service categories survive classification.
    parts = [part.strip(" \t,-") for part in _CANDIDATE_SEPARATOR_RE.split(cleaned) if part.strip(" \t,-")]
    merged = _merge_generic_context(parts)
    if merged:
        return merged[:8]

    # If punctuation was sparse, use category signal anchors as a second pass.
    # This handles input such as "garbage is uncollected streetlights are broken
    # and the road has potholes" while keeping the actual text for each ticket.
    normalized = cleaned.casefold()
    anchors: list[tuple[int, str]] = []
    for category, (_, signals) in CATEGORY_RULES.items():
        best: int | None = None
        for signal in signals:
            position = normalized.find(signal.casefold())
            if position >= 0 and (best is None or position < best):
                best = position
        if best is not None:
            anchors.append((best, category))

    anchors.sort(key=lambda item: item[0])
    distinct: list[tuple[int, str]] = []
    seen: set[str] = set()
    for position, category in anchors:
        if category not in seen:
            distinct.append((position, category))
            seen.add(category)

    if len(distinct) < 2:
        return [cleaned]

    slices: list[str] = []
    for index, (start, _) in enumerate(distinct):
        # Keep any introductory wording with the first detected issue.
        slice_start = 0 if index == 0 else start
        slice_end = distinct[index + 1][0] if index + 1 < len(distinct) else len(cleaned)
        value = cleaned[slice_start:slice_end].strip(" ,;:-")
        if value:
            slices.append(value)

    merged = _merge_generic_context(slices)
    return (merged or slices or [cleaned])[:8]


def _apply_shared_risk_context(issue: ComplaintAnalysis, full_text: str) -> None:
    value = full_text.casefold()
    if issue.priority == "MEDIUM" and any(term in value for term in _SHARED_RISK_TERMS):
        issue.priority = "HIGH"
        issue.urgency = "HIGH"
        issue.reasoning_summary = (
            f"The complaint was classified as {issue.category}. Priority is HIGH because the citizen described a shared "
            f"safety or public-health risk. Routing target: {issue.department}."
        )


def _verify_issue_location(issue: ComplaintAnalysis, cache: dict[str, LocationVerificationResponse]) -> None:
    if not issue.location:
        return
    key = issue.location.casefold().strip()
    verification = cache.get(key)
    if verification is None:
        verification = verify_location(issue.location)
        cache[key] = verification

    issue.location_verified = verification.valid
    issue.location_display_name = verification.canonical_name
    issue.location_verification_message = verification.message
    if verification.valid and verification.canonical_name:
        issue.location = verification.canonical_name
        if "location" in issue.missing_information:
            issue.missing_information.remove("location")
        issue.clarification_questions = [
            question
            for question in issue.clarification_questions
            if "location" not in question.casefold() and "area" not in question.casefold()
        ]
    elif not verification.valid:
        issue.location = None
        if "location" not in issue.missing_information:
            issue.missing_information.insert(0, "location")
        if verification.message not in issue.clarification_questions:
            issue.clarification_questions.insert(0, verification.message)
        issue.citizen_response = verification.message


@router.post("/complaints/analyze-batch-v2", response_model=ComplaintBatchAnalysis)
def analyze_batch_v2(
    payload: AnalyzeComplaintRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ComplaintBatchAnalysis:
    fragments = split_civic_issues(payload.complaint)
    issues = [
        analyze_complaint(fragment, supplied_location=payload.location, landmark=payload.landmark)
        for fragment in fragments
    ]

    verified_cache: dict[str, LocationVerificationResponse] = {}
    for issue in issues:
        _apply_shared_risk_context(issue, payload.complaint)
        if payload.verify_location:
            _verify_issue_location(issue, verified_cache)
        issue.duplicate_candidates = find_duplicates(db, issue, issue.source_text or payload.complaint)

    language, code, _ = detect_language(payload.complaint)
    return ComplaintBatchAnalysis(language=language, language_code=code, issue_count=len(issues), issues=issues)
