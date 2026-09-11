import re

from sqlalchemy.orm import Session

from ..models import User
from ..platform_schemas import AssistantAction, AssistantResponse
from .pipeline import analyze_complaints
from .platform import incidents, list_visible_tickets, meta_response
from .ticketing import get_ticket, to_response

TICKET_RE = re.compile(r"\bCR-\d{6}-[A-Z0-9]{6}\b", re.IGNORECASE)


def _ticket_summary(ticket) -> str:
    return f"{ticket.ticket_code}: {ticket.category} in {ticket.location} — {ticket.status.replace('_', ' ').title()} ({ticket.priority})."


def answer_assistant(db: Session, user: User, message: str) -> AssistantResponse:
    text = message.strip()
    low = text.casefold()
    ticket_match = TICKET_RE.search(text)

    if ticket_match:
        code = ticket_match.group(0).upper()
        try:
            ticket = get_ticket(db, code)
        except LookupError:
            return AssistantResponse(reply=f"I could not find ticket {code}.")
        if user.role == "CITIZEN" and ticket.submitted_by_user_id != user.id:
            return AssistantResponse(reply="I could not find that ticket in your account.")
        meta = meta_response(db, ticket)
        reply = _ticket_summary(ticket)
        if meta.related_reports > 1:
            reply += f" It is grouped with {meta.related_reports - 1} other related report(s)."
        if meta.emergency:
            reply += " This report carries a safety-risk flag for human review."
        return AssistantResponse(
            reply=reply,
            actions=[AssistantAction(type="OPEN_TICKET", label="Open ticket", value=code)],
            data={"ticket": to_response(ticket).model_dump(mode="json"), "meta": meta.model_dump(mode="json")},
        )

    if user.role == "CITIZEN" and any(term in low for term in ("my complaint", "my ticket", "unresolved", "pending complaint", "show complaints")):
        tickets = list_visible_tickets(db, user=user)
        if "unresolved" in low or "pending" in low:
            tickets = [t for t in tickets if t.status != "RESOLVED"]
        if not tickets:
            return AssistantResponse(reply="You do not have matching active complaints right now.")
        preview = "\n".join(_ticket_summary(t) for t in tickets[:5])
        return AssistantResponse(
            reply=f"Here are your latest matching complaints:\n{preview}",
            actions=[AssistantAction(type="SHOW_MY_TICKETS", label="Open my complaints")],
            data={"count": len(tickets)},
        )

    if user.role in {"OFFICER", "ADMIN"} and any(term in low for term in ("critical", "breach", "escalat", "queue", "incident", "unresolved")):
        tickets = list_visible_tickets(db, include_archived=False, staff=True)
        if "critical" in low:
            tickets = [t for t in tickets if t.priority == "CRITICAL"]
        if "breach" in low or "escalat" in low:
            tickets = [t for t in tickets if t.sla_state == "BREACHED" or t.status == "ESCALATED"]
        if "unresolved" in low:
            tickets = [t for t in tickets if t.status != "RESOLVED"]
        active_incidents = incidents(db)
        return AssistantResponse(
            reply=(
                f"I found {len(tickets)} matching ticket(s) and {len(active_incidents)} active incident cluster(s). "
                "Open Ticket operations to review, assign, transfer or resolve them."
            ),
            actions=[AssistantAction(type="OPEN_QUEUE", label="Open ticket operations")],
            data={"tickets": [to_response(t).model_dump(mode="json") for t in tickets[:10]], "incidents": [i.model_dump() for i in active_incidents[:10]]},
        )

    analyses = analyze_complaints(text)
    if analyses and any(a.category != "Other Civic Service" for a in analyses):
        summaries = [f"{i+1}. {a.category} → {a.department} ({a.priority})" for i, a in enumerate(analyses)]
        reply = "I identified the following civic issue" + ("s" if len(summaries) > 1 else "") + ":\n" + "\n".join(summaries)
        if user.role == "CITIZEN":
            reply += "\nYou can open Submit complaint to verify the location and create trackable ticket(s)."
            actions = [AssistantAction(type="CREATE_COMPLAINT", label="Use this in Submit complaint", value=text)]
        else:
            reply += "\nThis can be used to help triage an incoming citizen report."
            actions = [AssistantAction(type="OPEN_QUEUE", label="Open ticket operations")]
        return AssistantResponse(reply=reply, actions=actions, data={"issue_count": len(analyses)})

    role_help = (
        "I can help you create or understand a complaint, check a CR-* ticket, and show your active complaints."
        if user.role == "CITIZEN"
        else "I can inspect CR-* tickets, summarize critical or SLA-breached work, identify incident clusters, and triage complaint text."
    )
    return AssistantResponse(reply=role_help)
