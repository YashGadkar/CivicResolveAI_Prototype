import re
import time
from dataclasses import dataclass

from ..schemas import AgentStage, ComplaintAnalysis

CATEGORY_RULES = {
    "Water Supply": ("Water Supply Department", ["water", "पाणी", "पानी", "agua", "eau", "wasser", "água", "مياه", "পানি", "પાણી", "ਪਾਣੀ", "தண்ணீர்", "నీరు", "ನೀರು", "വെള്ളം", "停水", "断水", "단수"]),
    "Garbage Collection": ("Solid Waste Management Department", ["garbage", "waste", "trash", "कचरा", "कूड़ा", "basura", "déchets", "müll", "lixo", "قمامة", "আবর্জনা", "કચરો", "குப்பை", "చెత్త", "ಕಸ", "മാലിന്യം", "垃圾", "ゴミ", "쓰레기"]),
    "Roads & Potholes": ("Roads & Public Works Department", ["pothole", "broken road", "road damaged", "खड्डा", "गड्ढा", "bache", "nid-de-poule", "schlagloch", "حفرة", "গর্ত", "குழி", "రోడ్డు గుంత", "ಗುಂಡಿ", "റോഡ് കുഴി", "坑洼", "道路破損", "포트홀"]),
    "Streetlights": ("Street Lighting Department", ["streetlight", "street light", "lamp post", "पथदिवा", "स्ट्रीट लाइट", "farola", "éclairage public", "straßenlaterne", "إنارة الشوارع", "রাস্তার আলো", "தெருவிளக்கு", "వీధి దీపం", "ಬೀದಿ ದೀಪ", "തെരുവ് വിളക്ക്", "路灯", "街灯", "가로등"]),
    "Drainage & Sewage": ("Drainage & Sewerage Department", ["drainage", "sewage", "sewer", "गटार", "सीवर", "alcantarillado", "égout", "abwasser", "esgoto", "صرف صحي", "নর্দমা", "சாக்கடை", "కాలువ", "ಚರಂಡಿ", "അഴുക്കുചാൽ", "下水道", "하수구"]),
    "Electricity": ("Electrical Services Department", ["electricity", "power outage", "no power", "transformer", "वीज", "बिजली", "electricidad", "électricité", "stromausfall", "energia", "الكهرباء", "বিদ্যুৎ", "மின்சாரம்", "కరెంట్", "ವಿದ್ಯುತ್", "വൈദ്യുതി", "停电", "停電", "정전"]),
    "Public Transport": ("Public Transport Department", ["bus", "public transport", "metro", "बस", "autobús", "transport public", "公交", "公共交通"]),
    "Sanitation": ("Sanitation Department", ["public toilet", "sanitation", "शौचालय", "स्वच्छता", "baño público", "toilettes publiques"]),
    "Public Health": ("Public Health Department", ["mosquito", "dengue", "health hazard", "डेंग्यू", "आरोग्य", "moustique", "بعوض", "ডেঙ্গু"]),
    "Parks & Environment": ("Parks & Environment Department", ["park", "tree fallen", "pollution", "झाड", "उद्यान", "parque", "umwelt", "تلوث", "公园"]),
    "Traffic & Parking": ("Traffic Management Department", ["traffic", "parking", "congestion", "वाहतूक", "पार्किंग", "tráfico", "stationnement", "verkehr", "مرور", "交通"]),
    "Construction & Encroachment": ("Encroachment & Building Department", ["encroachment", "illegal construction", "अतिक्रमण", "बांधकाम", "construcción ilegal", "construction illégale", "تعدي"]),
    "Stray Animals": ("Animal Welfare & Control Department", ["stray dog", "stray animal", "dog attack", "भटके कुत्रे", "आवारा कुत्ते", "perro callejero", "chien errant", "كلب ضال"]),
    "Noise Pollution": ("Environment & Enforcement Department", ["noise", "loudspeaker", "loud music", "आवाज", "शोर", "ruido", "bruit", "lärm", "ضوضاء"]),
    "Public Safety": ("Civic Safety Coordination Cell", ["danger", "unsafe", "open manhole", "collapsed", "fire", "धोका", "अपघात", "peligro", "dangereux", "خطر", "危险"]),
}

ACTIONS = {
    "Water Supply": ["Verify supply interruption and pipeline/valve status.", "Dispatch a field inspection if required.", "Publish a restoration update."],
    "Garbage Collection": ["Confirm the missed collection route.", "Schedule priority pickup and sanitation inspection.", "Record collection completion."],
    "Roads & Potholes": ["Inspect and mark the road hazard.", "Schedule temporary and permanent repair.", "Maintain traffic safety controls until repaired."],
    "Streetlights": ["Verify the pole and electrical feed.", "Assign a maintenance crew.", "Confirm illumination after repair."],
    "Drainage & Sewage": ["Inspect blockage and overflow extent.", "Deploy cleaning/desilting crew.", "Review recurring blockage causes."],
    "Electricity": ["Verify outage scope and electrical equipment condition.", "Dispatch an authorized crew.", "Provide restoration and safety guidance."],
}
DEFAULT_ACTIONS = ["Validate the affected civic service.", "Assign the correct operational team.", "Update the citizen with the next action and expected timeline."]

SCRIPT_RULES = [
    (r"[\u0980-\u09FF]", "Bengali", "bn", "Bengali"), (r"[\u0A80-\u0AFF]", "Gujarati", "gu", "Gujarati"),
    (r"[\u0A00-\u0A7F]", "Punjabi", "pa", "Gurmukhi"), (r"[\u0B80-\u0BFF]", "Tamil", "ta", "Tamil"),
    (r"[\u0C00-\u0C7F]", "Telugu", "te", "Telugu"), (r"[\u0C80-\u0CFF]", "Kannada", "kn", "Kannada"),
    (r"[\u0D00-\u0D7F]", "Malayalam", "ml", "Malayalam"), (r"[\u0B00-\u0B7F]", "Odia", "or", "Odia"),
    (r"[\u0E00-\u0E7F]", "Thai", "th", "Thai"), (r"[\u3040-\u30FF]", "Japanese", "ja", "Japanese Kana"),
    (r"[\uAC00-\uD7AF]", "Korean", "ko", "Hangul"), (r"[\u4E00-\u9FFF]", "Chinese", "zh", "Han"),
    (r"[\u0370-\u03FF]", "Greek", "el", "Greek"), (r"[\u0590-\u05FF]", "Hebrew", "he", "Hebrew"),
]
LATIN_HINTS = [
    ("Spanish", "es", [" no hay ", " agua ", " basura ", " calle "]), ("French", "fr", [" pas de ", " eau ", " déchets ", " rue "]),
    ("German", "de", [" kein ", " wasser ", " müll ", " straße "]), ("Portuguese", "pt", [" não ", " água ", " lixo ", " rua "]),
    ("Italian", "it", [" non ", " acqua ", " rifiuti ", " strada "]), ("Indonesian", "id", [" tidak ", " jalan ", " sampah ", " listrik "]),
]
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाच": 5, "दोन": 2, "uno": 1, "dos": 2, "tres": 3}
LOCATION_QUESTIONS = {"mr": "कृपया परिसर, वॉर्ड किंवा जवळचे ठिकाण सांगा.", "hi": "कृपया क्षेत्र, वार्ड या नज़दीकी स्थान बताएं।", "es": "Indique su zona, barrio, distrito o punto de referencia más cercano.", "fr": "Veuillez indiquer votre quartier, secteur ou point de repère le plus proche.", "ar": "يرجى ذكر المنطقة أو الحي أو أقرب معلم.", "bn": "অনুগ্রহ করে এলাকা, ওয়ার্ড বা কাছাকাছি কোনো পরিচিত স্থান লিখুন।", "ta": "உங்கள் பகுதி, வார்டு அல்லது அருகிலுள்ள அடையாளத்தை குறிப்பிடவும்."}


@dataclass
class StageTimer:
    name: str
    started: float

    @classmethod
    def start(cls, name: str) -> "StageTimer":
        return cls(name, time.perf_counter())

    def finish(self, status: str, output: str) -> AgentStage:
        return AgentStage(name=self.name, status=status, output=output, processing_ms=max(1, round((time.perf_counter() - self.started) * 1000)))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def detect_language(text: str) -> tuple[str, str, str]:
    for pattern, language, code, script in SCRIPT_RULES:
        if re.search(pattern, text):
            return language, code, script
    if re.search(r"[\u0900-\u097F]", text):
        marathi = any(word in text for word in ("आहे", "नाही", "पासून", "भागात", "पाणी", "रस्ता", "कचरा"))
        return ("Marathi", "mr", "Devanagari") if marathi else ("Hindi", "hi", "Devanagari")
    if re.search(r"[\u0600-\u06FF]", text):
        if any(ch in text for ch in ("ے", "ں", "ٹ", "ڈ", "ڑ")):
            return "Urdu", "ur", "Arabic"
        if any(ch in text for ch in ("گ", "چ", "پ", "ژ")):
            return "Persian", "fa", "Arabic"
        return "Arabic", "ar", "Arabic"
    if re.search(r"[\u0400-\u04FF]", text):
        return ("Ukrainian", "uk", "Cyrillic") if any(ch in text.lower() for ch in ("і", "ї", "є", "ґ")) else ("Russian", "ru", "Cyrillic")
    padded = f" {normalize(text)} "
    for language, code, hints in LATIN_HINTS:
        if sum(hint in padded for hint in hints) >= 2:
            return language, code, "Latin"
    return "English", "en", "Latin"


def classify(text: str) -> tuple[str, float]:
    value = normalize(text)
    tokens = set(re.findall(r"\w+", value, flags=re.UNICODE))
    scores = {}
    for category, (_, signals) in CATEGORY_RULES.items():
        score = 0.0
        for signal in signals:
            sig = signal.casefold()
            if sig in value:
                score += 3 if " " in sig else 2
            else:
                parts = set(re.findall(r"\w+", sig, flags=re.UNICODE))
                if parts and len(parts & tokens) / len(parts) >= 0.66:
                    score += 1
        scores[category] = score
    category, score = max(scores.items(), key=lambda item: item[1])
    return ("Other Civic Service", 0.56) if score <= 0 else (category, min(0.97, 0.72 + score * 0.035))


def extract_duration(text: str) -> tuple[str | None, float | None]:
    value = normalize(text)
    units = r"day|days|week|weeks|hour|hours|दिवस|दिवसांपासून|दिन|दिनों|हफ्ते|आठवड|día|días|jour|jours|tag|tage|يوم|أيام|দিন|நாள்|రోజు|రోజులు|ದಿನ|ദിവസം|天|日"
    match = re.search(rf"(\d+)\s*({units})", value)
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        days = amount * 7 if unit.startswith(("week", "हफ्त", "आठवड")) else amount / 24 if unit.startswith("hour") else amount
        return f"{amount} {unit}", float(days)
    for word, amount in NUMBER_WORDS.items():
        if word in value and re.search(units, value):
            return f"{word} days", float(amount)
    return None, None


def extract_location(text: str, supplied: str | None) -> str | None:
    if supplied and supplied.strip():
        return supplied.strip()
    match = re.search(r"\b(?:in|at|near|around|outside)\s+([A-Z][A-Za-z.-]+(?:\s+[A-Z][A-Za-z.-]+){0,3})", text)
    if not match:
        return None
    candidate = match.group(1).strip(" .,!?:;")
    return None if normalize(candidate) in {"our area", "my area", "our street", "my street"} else candidate


def determine_priority(category: str, text: str, duration_days: float | None) -> tuple[str, str]:
    value = normalize(text)
    if any(term in value for term in ("fire", "collapsed", "live wire", "open manhole", "life threatening", "immediate danger", "जीवाला धोका", "خطر فوري", "危险")):
        return "CRITICAL", "Immediate public-safety risk detected."
    if any(term in value for term in ("several bikes", "nearly fallen", "accident", "nobody is responding", "starting to smell", "overflow", "sparking", "unsafe", "school", "dangerous", "peligro", "خطر")):
        return "HIGH", "Complaint indicates elevated safety, health, or service-impact risk."
    if category in {"Water Supply", "Electricity", "Drainage & Sewage", "Public Health"} and duration_days is not None and duration_days >= 3:
        return "HIGH", "Essential civic service has been disrupted for an extended period."
    if category == "Garbage Collection" and duration_days is not None and duration_days >= 3:
        return "HIGH", "Prolonged waste accumulation can create a sanitation risk."
    return "MEDIUM", "Service disruption requires action but no critical hazard was detected."


def citizen_message(code: str, category: str, department: str, missing: list[str]) -> str:
    if "location" in missing:
        return LOCATION_QUESTIONS.get(code, "We understood your complaint. Please provide your area, locality, ward, or nearest landmark so it can be routed correctly.")
    if code == "mr":
        return f"आपली {category} तक्रार नोंदवण्यासाठी तयार आहे. ती {department} कडे पाठवली जाईल."
    if code == "hi":
        return f"आपकी {category} शिकायत टिकट बनाने के लिए तैयार है और इसे {department} को भेजा जाएगा।"
    return f"Your {category} complaint is ready for ticket creation and routing to the {department}."


def analyze_complaint(complaint: str, selected_language: str = "Auto", supplied_location: str | None = None, landmark: str | None = None) -> ComplaintAnalysis:
    del selected_language
    trace: list[AgentStage] = []
    timer = StageTimer.start("Language Detection Agent")
    language, code, script = detect_language(complaint)
    trace.append(timer.finish("COMPLETED", f"Detected {language} ({code}) from {script} script/features."))

    timer = StageTimer.start("Complaint Understanding Agent")
    category, confidence = classify(complaint)
    trace.append(timer.finish("COMPLETED", f"Civic intent classified as {category} with {confidence:.0%} confidence."))

    timer = StageTimer.start("Entity & Location Agent")
    duration, duration_days = extract_duration(complaint)
    location = extract_location(complaint, supplied_location)
    trace.append(timer.finish("COMPLETED", f"duration={duration or 'not stated'}; location={location or 'missing'}" + (f"; landmark={landmark}" if landmark else "")))

    timer = StageTimer.start("Priority & Urgency Agent")
    priority, reason = determine_priority(category, complaint, duration_days)
    trace.append(timer.finish("COMPLETED", f"{priority} — {reason}"))

    timer = StageTimer.start("Missing Information Agent")
    missing, questions = [], []
    if not location:
        missing.append("location")
        questions.append(LOCATION_QUESTIONS.get(code, "Please provide your area, locality, ward or nearest landmark."))
    if category == "Other Civic Service":
        missing.append("service context")
        questions.append("Please add what civic service is affected and what action you need from the authority.")
    trace.append(timer.finish("ACTION REQUIRED" if missing else "COMPLETED", ", ".join(missing) if missing else "Required routing information is available."))

    department = CATEGORY_RULES.get(category, ("Citizen Services Coordination Cell", []))[0]
    timer = StageTimer.start("Department Routing Agent")
    trace.append(timer.finish("COMPLETED", f"Routed to {department} based on the detected complaint category."))
    recommendations = ACTIONS.get(category, DEFAULT_ACTIONS)

    timer = StageTimer.start("Ticket Agent")
    trace.append(timer.finish("ACTION REQUIRED" if missing else "WAITING", "Waiting for required clarification before ticket creation." if missing else "Ready to create a persistent ticket."))
    timer = StageTimer.start("Resolution Recommendation Agent")
    trace.append(timer.finish("WAITING" if missing else "COMPLETED", recommendations[0]))
    response = citizen_message(code, category, department, missing)
    timer = StageTimer.start("Citizen Response Agent")
    trace.append(timer.finish("COMPLETED", response))
    timer = StageTimer.start("SLA Monitoring Agent")
    trace.append(timer.finish("WAITING", "SLA countdown begins after ticket creation."))
    timer = StageTimer.start("Escalation Agent")
    trace.append(timer.finish("WAITING", "Escalation activates only if the configured prototype SLA is breached."))

    return ComplaintAnalysis(
        category=category, location=location, landmark=landmark, duration=duration, priority=priority, urgency=priority,
        department=department, missing_information=missing, clarification_questions=questions,
        resolution_recommendation=recommendations, language=language, language_code=code, detected_script=script,
        analysis_mode="Automatic multilingual deterministic analysis", confidence=round(confidence, 2),
        reasoning_summary=f"Language was detected automatically as {language}. The complaint was classified as {category} with {confidence:.0%} confidence. Priority is {priority} because {reason.lower()} Routing target: {department}.",
        citizen_response=response, agent_trace=trace,
    )
