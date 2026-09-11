import re
import time
from dataclasses import dataclass

from ..schemas import AgentStage, ComplaintAnalysis


CATEGORY_RULES: dict[str, dict] = {
    "Water Supply": {
        "department": "Water Supply Department",
        "signals": [
            "water supply", "no water", "water not", "tap water", "pipeline", "low pressure",
            "पाणी", "पाणी येत नाही", "जलापूर्ति", "पानी नहीं", "पानी की",
        ],
        "actions": [
            "Verify supply interruption and valve/pipeline status for the reported locality.",
            "Dispatch a field inspection if the outage is not part of planned maintenance.",
            "Publish an estimated restoration update for affected citizens.",
        ],
    },
    "Garbage Collection": {
        "department": "Solid Waste Management Department",
        "signals": ["garbage", "waste", "trash", "not collected", "कचरा", "कूड़ा", "कचरा उचल"],
        "actions": [
            "Confirm missed collection route and assigned vehicle.",
            "Schedule priority pickup and sanitation inspection.",
            "Record collection completion with location evidence.",
        ],
    },
    "Roads & Potholes": {
        "department": "Roads & Public Works Department",
        "signals": ["pothole", "road damaged", "broken road", "crater", "खड्डा", "रस्ता खराब", "गड्ढा", "सड़क"],
        "actions": [
            "Inspect road hazard and mark the unsafe area.",
            "Schedule temporary patching followed by permanent repair.",
            "Prioritize traffic safety controls until repair is complete.",
        ],
    },
    "Streetlights": {
        "department": "Street Lighting Department",
        "signals": ["streetlight", "street light", "lamp post", "dark street", "दिवा", "पथदिवा", "स्ट्रीट लाइट"],
        "actions": [
            "Verify pole identifier and electrical feed.",
            "Assign maintenance crew for lamp, wiring, or controller repair.",
            "Confirm illumination after repair.",
        ],
    },
    "Drainage & Sewage": {
        "department": "Drainage & Sewerage Department",
        "signals": ["drainage", "sewage", "sewer", "drain overflow", "gutter", "नाला", "गटार", "सीवर"],
        "actions": [
            "Inspect blockage and overflow extent.",
            "Deploy cleaning/desilting crew and isolate public-health hazards.",
            "Check recurring blockage causes after flow is restored.",
        ],
    },
    "Electricity": {
        "department": "Electrical Services Department",
        "signals": ["power outage", "electricity", "no power", "transformer", "wire sparking", "वीज", "बिजली"],
        "actions": [
            "Verify outage scope and feeder/transformer condition.",
            "Dispatch an authorized electrical crew for safety assessment.",
            "Provide restoration estimate and hazard notice where required.",
        ],
    },
    "Public Transport": {
        "department": "Public Transport Department",
        "signals": ["bus", "public transport", "bus stop", "route cancelled", "metro", "बस", "वाहतूक सेवा"],
        "actions": [
            "Validate affected route, stop, and service window.",
            "Coordinate with the operating control room.",
            "Publish service correction or alternate-route guidance.",
        ],
    },
    "Sanitation": {
        "department": "Sanitation Department",
        "signals": ["public toilet", "sanitation", "unclean toilet", "cleaning", "स्वच्छता", "शौचालय"],
        "actions": [
            "Inspect sanitation condition and health risk.",
            "Assign cleaning/disinfection team.",
            "Record completion and recurring maintenance requirement.",
        ],
    },
    "Public Health": {
        "department": "Public Health Department",
        "signals": ["mosquito", "dengue", "disease", "health hazard", "contaminated", "डेंग्यू", "आरोग्य"],
        "actions": [
            "Assess the reported public-health risk.",
            "Coordinate inspection, sampling, or vector-control response.",
            "Issue preventive guidance to affected residents.",
        ],
    },
    "Parks & Environment": {
        "department": "Parks & Environment Department",
        "signals": ["park", "tree fallen", "tree cutting", "pollution", "garden", "झाड", "उद्यान", "प्रदूषण"],
        "actions": [
            "Inspect the environmental or park issue.",
            "Assign the appropriate horticulture/environment team.",
            "Document remediation and public-safety controls.",
        ],
    },
    "Traffic & Parking": {
        "department": "Traffic Management Department",
        "signals": ["traffic", "illegal parking", "parking", "signal not working", "congestion", "वाहतूक", "पार्किंग"],
        "actions": [
            "Verify congestion or parking obstruction at the reported location.",
            "Coordinate enforcement or signal maintenance as applicable.",
            "Monitor traffic normalization after action.",
        ],
    },
    "Construction & Encroachment": {
        "department": "Encroachment & Building Department",
        "signals": ["encroachment", "illegal construction", "construction debris", "footpath blocked", "अतिक्रमण", "बांधकाम"],
        "actions": [
            "Verify site ownership/permit context and obstruction.",
            "Assign inspection to the authorized civic team.",
            "Record notice, clearance, or enforcement outcome.",
        ],
    },
    "Stray Animals": {
        "department": "Animal Welfare & Control Department",
        "signals": ["stray dog", "stray animal", "dog attack", "cattle road", "भटके कुत्रे", "आवारा कुत्ते"],
        "actions": [
            "Assess immediate public-safety risk and animal condition.",
            "Dispatch trained animal-control/welfare personnel.",
            "Record humane relocation or treatment outcome.",
        ],
    },
    "Noise Pollution": {
        "department": "Environment & Enforcement Department",
        "signals": ["noise", "loudspeaker", "loud music", "construction noise", "ध्वनी", "आवाज", "शोर"],
        "actions": [
            "Validate time, source, and persistence of excessive noise.",
            "Coordinate measurement/enforcement where applicable.",
            "Record corrective action and repeat-offence status.",
        ],
    },
    "Public Safety": {
        "department": "Civic Safety Coordination Cell",
        "signals": ["danger", "unsafe", "accident risk", "open manhole", "collapsed", "fire", "धोका", "अपघात"],
        "actions": [
            "Secure the immediate hazard area.",
            "Notify the responsible emergency/civic response team.",
            "Maintain escalation until the public-safety risk is removed.",
        ],
    },
}

GENERIC_LOCATION_WORDS = {
    "our area", "my area", "our street", "my street", "nearby", "here",
    "आमच्या भागात", "माझ्या भागात", "हमारे इलाके", "मेरे इलाके",
}

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाच": 5, "दोन": 2,
}


@dataclass
class StageTimer:
    name: str
    started: float

    @classmethod
    def start(cls, name: str) -> "StageTimer":
        return cls(name=name, started=time.perf_counter())

    def finish(self, status: str, output: str) -> AgentStage:
        # Keep timings honest while ensuring ultra-fast local execution is still visible in UI.
        ms = max(1, round((time.perf_counter() - self.started) * 1000))
        return AgentStage(name=self.name, status=status, output=output, processing_ms=ms)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def detect_language(text: str, selected: str) -> str:
    if selected and selected.lower() not in {"auto", "detect"}:
        return selected.title()
    if re.search(r"[\u0900-\u097F]", text):
        marathi_hints = ("आहे", "नाही", "पासून", "भागात", "पाणी", "रस्ता")
        return "Marathi" if any(h in text for h in marathi_hints) else "Hindi"
    return "English"


def classify(text: str) -> tuple[str, float]:
    normalized = _normalize(text)
    scores: dict[str, float] = {}
    for category, rule in CATEGORY_RULES.items():
        score = 0.0
        for signal in rule["signals"]:
            sig = signal.casefold()
            if sig in normalized:
                score += 3.0 if " " in sig else 2.0
            else:
                sig_tokens = set(re.findall(r"\w+", sig, flags=re.UNICODE))
                text_tokens = set(re.findall(r"\w+", normalized, flags=re.UNICODE))
                if sig_tokens and len(sig_tokens & text_tokens) / len(sig_tokens) >= 0.66:
                    score += 1.0
        scores[category] = score

    category, score = max(scores.items(), key=lambda item: item[1])
    if score <= 0:
        return "Other Civic Service", 0.58
    confidence = min(0.97, 0.72 + score * 0.035)
    return category, confidence


def extract_duration(text: str) -> tuple[str | None, float | None]:
    normalized = _normalize(text)
    digit_match = re.search(
        r"(\d+)\s*(day|days|week|weeks|hour|hours|दिवस|दिवसांपासून|दिन|दिनों|हफ्ते|आठवड)",
        normalized,
    )
    if digit_match:
        value = int(digit_match.group(1))
        unit = digit_match.group(2)
        days = value
        if unit.startswith(("week", "हफ्त", "आठवड")):
            days = value * 7
        elif unit.startswith(("hour",)):
            days = value / 24
        label = f"{value} {unit}"
        return label, float(days)

    for word, value in NUMBER_WORDS.items():
        if word in normalized:
            if any(unit in normalized for unit in ("week", "हफ्त", "आठवड")):
                return f"{word} weeks", float(value * 7)
            if any(unit in normalized for unit in ("day", "days", "दिवस", "दिन")):
                return f"{word} days", float(value)
    return None, None


def extract_location(text: str, supplied: str | None) -> str | None:
    if supplied and supplied.strip():
        return supplied.strip()

    for generic in GENERIC_LOCATION_WORDS:
        if generic in _normalize(text):
            # Do not mistake "our area/street" for an actionable locality.
            break

    # Conservative extraction: explicit preposition followed by title-cased locality.
    match = re.search(
        r"\b(?:in|at|near|around|outside)\s+([A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+){0,3})",
        text,
    )
    if match:
        candidate = match.group(1).strip(" .,!?:;")
        if _normalize(candidate) not in GENERIC_LOCATION_WORDS:
            return candidate
    return None


def determine_priority(category: str, text: str, duration_days: float | None) -> tuple[str, str]:
    normalized = _normalize(text)
    critical = (
        "fire", "collapsed", "live wire", "electrocution", "open manhole",
        "severe flooding", "life threatening", "immediate danger", "जीवाला धोका",
    )
    if any(term in normalized for term in critical):
        return "CRITICAL", "Immediate public-safety risk detected."

    high_risk = (
        "several bikes", "nearly fallen", "accident", "nobody is responding",
        "starting to smell", "overflow", "sparking", "unsafe", "school",
    )
    essential = category in {"Water Supply", "Electricity", "Drainage & Sewage", "Public Health"}
    if any(term in normalized for term in high_risk):
        return "HIGH", "Complaint indicates elevated safety, health, or service-impact risk."
    if essential and duration_days is not None and duration_days >= 3:
        return "HIGH", "Essential civic service has been disrupted for an extended period."
    if category == "Garbage Collection" and duration_days is not None and duration_days >= 3:
        return "HIGH", "Prolonged waste accumulation can create a sanitation risk."
    if category == "Streetlights" and duration_days is not None and duration_days >= 7:
        return "MEDIUM", "Persistent lighting failure raises neighborhood safety concerns."
    if category == "Other Civic Service":
        return "MEDIUM", "Impact is not yet specific enough for a lower or higher priority."
    return "MEDIUM", "Service disruption requires action but no critical hazard was detected."


def citizen_message(language: str, category: str, department: str, missing: list[str]) -> str:
    needs_location = "location" in missing
    if language.lower() == "marathi":
        if needs_location:
            return "तक्रार समजली आहे. कृपया परिसर, वॉर्ड किंवा जवळचे ठिकाण द्या, म्हणजे तक्रार योग्य विभागाकडे पाठवता येईल."
        return f"आपली {category} तक्रार नोंदवण्यासाठी तयार आहे. ती {department} कडे पाठवली जाईल."
    if language.lower() == "hindi":
        if needs_location:
            return "शिकायत समझ ली गई है। कृपया क्षेत्र, वार्ड या नज़दीकी स्थान बताएं ताकि इसे सही विभाग तक भेजा जा सके।"
        return f"आपकी {category} शिकायत टिकट बनाने के लिए तैयार है और इसे {department} को भेजा जाएगा."
    if needs_location:
        return "We understood your complaint. Please provide your area, locality, ward, or nearest landmark so it can be routed correctly."
    return f"Your {category} complaint is ready for ticket creation and routing to the {department}."


def analyze_complaint(
    complaint: str,
    selected_language: str = "English",
    supplied_location: str | None = None,
    landmark: str | None = None,
) -> ComplaintAnalysis:
    trace: list[AgentStage] = []

    timer = StageTimer.start("Complaint Understanding Agent")
    language = detect_language(complaint, selected_language)
    trace.append(timer.finish("COMPLETED", f"Detected/selected language: {language}; complaint intent normalized."))

    timer = StageTimer.start("Entity & Location Agent")
    duration, duration_days = extract_duration(complaint)
    location = extract_location(complaint, supplied_location)
    entity_bits = [f"duration={duration or 'not stated'}", f"location={location or 'missing'}"]
    if landmark:
        entity_bits.append(f"landmark={landmark}")
    trace.append(timer.finish("COMPLETED", "; ".join(entity_bits)))

    timer = StageTimer.start("Priority & Urgency Agent")
    category, confidence = classify(complaint)
    priority, priority_reason = determine_priority(category, complaint, duration_days)
    trace.append(timer.finish("COMPLETED", f"{priority} — {priority_reason}"))

    timer = StageTimer.start("Missing Information Agent")
    missing: list[str] = []
    questions: list[str] = []
    if not location:
        missing.append("location")
        questions.append("Please provide your area, locality, ward or nearest landmark.")
    if category == "Other Civic Service":
        missing.append("service context")
        questions.append("Please add what civic service is affected and what action you need from the authority.")
    mi_status = "ACTION REQUIRED" if missing else "COMPLETED"
    mi_output = ", ".join(missing) if missing else "Required routing information is available."
    trace.append(timer.finish(mi_status, mi_output))

    timer = StageTimer.start("Department Routing Agent")
    department = CATEGORY_RULES.get(category, {}).get("department", "Citizen Services Coordination Cell")
    trace.append(timer.finish("COMPLETED", f"Routed to {department} based on classified civic intent."))

    recommendations = CATEGORY_RULES.get(category, {}).get(
        "actions",
        [
            "Review the complaint and validate the responsible civic service.",
            "Assign the complaint to the correct operational team.",
            "Update the citizen with the next action and expected timeline.",
        ],
    )

    timer = StageTimer.start("Ticket Agent")
    trace.append(
        timer.finish(
            "ACTION REQUIRED" if missing else "WAITING",
            "Waiting for required clarification before ticket creation." if missing else "Ready to create a persistent ticket.",
        )
    )

    timer = StageTimer.start("Resolution Recommendation Agent")
    trace.append(timer.finish("WAITING" if missing else "COMPLETED", recommendations[0]))

    timer = StageTimer.start("Citizen Response Agent")
    response = citizen_message(language, category, department, missing)
    trace.append(timer.finish("COMPLETED", response))

    timer = StageTimer.start("SLA Monitoring Agent")
    trace.append(timer.finish("WAITING", "SLA countdown begins after ticket creation."))

    timer = StageTimer.start("Escalation Agent")
    trace.append(timer.finish("WAITING", "Escalation activates only if the configured prototype SLA is breached."))

    reasoning = (
        f"Intent classified as {category} with {confidence:.0%} deterministic confidence. "
        f"Priority {priority} because {priority_reason.lower()} "
        f"Routing target: {department}."
    )

    return ComplaintAnalysis(
        category=category,
        location=location,
        landmark=landmark,
        duration=duration,
        priority=priority,
        urgency=priority,
        department=department,
        missing_information=missing,
        clarification_questions=questions,
        resolution_recommendation=recommendations,
        language=language,
        confidence=round(confidence, 2),
        reasoning_summary=reasoning,
        citizen_response=response,
        agent_trace=trace,
    )
