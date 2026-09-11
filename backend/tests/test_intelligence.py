from app.services.location import verify_location
from app.services.pipeline import analyze_complaints, detect_language


def test_multiple_english_problems_are_separated():
    result = analyze_complaints(
        "There is no water supply for three days and garbage has not been collected for five days.",
        supplied_location="Rahuri",
    )
    assert [issue.category for issue in result] == ["Water Supply", "Garbage Collection"]


def test_multiple_marathi_problems_are_separated():
    result = analyze_complaints(
        "आमच्या भागात पाणी येत नाही आणि कचरा तीन दिवसांपासून उचललेला नाही.",
        supplied_location="Rahuri",
    )
    assert [issue.category for issue in result] == ["Water Supply", "Garbage Collection"]
    assert all(issue.language == "Marathi" for issue in result)


def test_language_detection_across_scripts():
    assert detect_language("No hay agua en nuestra calle desde hace tres días.")[0] == "Spanish"
    assert detect_language("எங்கள் பகுதியில் தெருவிளக்கு வேலை செய்யவில்லை.")[0] == "Tamil"
    assert detect_language("هناك انقطاع الكهرباء في الحي.")[0] == "Arabic"


def test_obviously_fake_location_is_rejected_without_network():
    result = verify_location("asdf")
    assert result.valid is False
    assert "real locality" in result.message
