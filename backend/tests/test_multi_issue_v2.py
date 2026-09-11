from app.intelligence_routes import split_civic_issues
from app.services.pipeline import classify


def categories(text: str) -> list[str]:
    return [classify(part)[0] for part in split_civic_issues(text)]


def test_comma_separated_three_service_failures_are_split():
    text = (
        "I am writing to formally report a critical municipal failure regarding uncollected garbage, "
        "broken streetlights, severe potholes which require immediate intervention due to escalating "
        "safety and public health risks to local residents."
    )
    assert categories(text) == ["Garbage Collection", "Streetlights", "Roads & Potholes"]


def test_address_comma_does_not_create_fake_issue():
    text = "Garbage has not been collected near Akurdi, Pune for three days."
    parts = split_civic_issues(text)
    assert len(parts) == 1
    assert classify(parts[0])[0] == "Garbage Collection"


def test_conjunction_separates_distinct_services():
    text = "Garbage is overflowing and the streetlights are broken and the road has several potholes."
    assert categories(text) == ["Garbage Collection", "Streetlights", "Roads & Potholes"]
