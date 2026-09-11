import pytest

from app.services.pipeline import analyze_complaint


@pytest.mark.parametrize(
    ("text", "category", "priority"),
    [
        (
            "There has been no water supply in our area for three days and nobody is responding.",
            "Water Supply",
            "HIGH",
        ),
        (
            "There is a huge pothole near our college and several bikes have nearly fallen.",
            "Roads & Potholes",
            "HIGH",
        ),
        (
            "Garbage has not been collected from our street for five days and it is starting to smell.",
            "Garbage Collection",
            "HIGH",
        ),
        (
            "The streetlight outside our building has been broken for two weeks.",
            "Streetlights",
            "MEDIUM",
        ),
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
    assert first.department == "Water Supply Department"

    clarified = analyze_complaint(text, supplied_location="Shivaji Nagar")
    assert clarified.location == "Shivaji Nagar"
    assert clarified.missing_information == []
    assert clarified.department == "Water Supply Department"


def test_marathi_water_scenario():
    result = analyze_complaint("आमच्या भागात तीन दिवसांपासून पाणी येत नाही.", selected_language="Marathi")
    assert result.category == "Water Supply"
    assert result.priority == "HIGH"
    assert result.location is None
    assert "location" in result.missing_information


def test_unknown_fails_safe_to_other():
    result = analyze_complaint("A strange civic issue is happening and I need the municipality to inspect it.")
    assert result.category == "Other Civic Service"
    assert result.clarification_questions
