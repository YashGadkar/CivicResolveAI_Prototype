import pytest

from app.services.pipeline import analyze_complaint


@pytest.mark.parametrize(
    ("text", "category", "priority"),
    [
        ("There has been no water supply in our area for three days and nobody is responding.", "Water Supply", "HIGH"),
        ("There is a huge pothole near our college and several bikes have nearly fallen.", "Roads & Potholes", "HIGH"),
        ("Garbage has not been collected from our street for five days and it is starting to smell.", "Garbage Collection", "HIGH"),
        ("The streetlight outside our building has been broken for two weeks.", "Streetlights", "MEDIUM"),
    ],
)
def test_acceptance_classification(text, category, priority):
    result = analyze_complaint(text)
    assert result.category == category
    assert result.priority == priority


def test_water_requires_location_then_accepts_clarification():
    text = "There has been no water supply in our area for three days and nobody is responding."
    first = analyze_complaint(text)
    assert first.location is None
    assert "location" in first.missing_information
    clarified = analyze_complaint(text, supplied_location="Shivaji Nagar")
    assert clarified.location == "Shivaji Nagar"
    assert clarified.missing_information == []


def test_language_is_detected_automatically_and_ignores_manual_label():
    result = analyze_complaint("आमच्या भागात तीन दिवसांपासून पाणी येत नाही.", selected_language="English")
    assert result.language == "Marathi"
    assert result.language_code == "mr"
    assert result.category == "Water Supply"
    assert result.priority == "HIGH"


@pytest.mark.parametrize(
    ("text", "language", "category"),
    [
        ("No hay agua en nuestra calle desde hace 3 días.", "Spanish", "Water Supply"),
        ("هناك انقطاع الكهرباء في الحي منذ يومين.", "Arabic", "Electricity"),
        ("எங்கள் பகுதியில் தெருவிளக்கு இரண்டு நாட்களாக வேலை செய்யவில்லை.", "Tamil", "Streetlights"),
        ("আমাদের এলাকায় আবর্জনা পাঁচ দিন ধরে সংগ্রহ করা হয়নি।", "Bengali", "Garbage Collection"),
    ],
)
def test_multilingual_language_and_problem_detection(text, language, category):
    result = analyze_complaint(text)
    assert result.language == language
    assert result.category == category
    assert result.agent_trace[0].name == "Language Detection Agent"


def test_unknown_fails_safe_to_other():
    result = analyze_complaint("A strange civic issue is happening and I need the municipality to inspect it.")
    assert result.category == "Other Civic Service"
    assert result.clarification_questions
