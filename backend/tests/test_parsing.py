import pytest
from services.sam_gov import _parse_opportunity, _parse_contact
from tests.conftest import SAMPLE_OPPORTUNITY, AWARD_OPPORTUNITY


def test_parse_full_opportunity():
    c = _parse_opportunity(SAMPLE_OPPORTUNITY)
    assert c is not None
    assert c.notice_id == "abc123"
    assert c.title == "IT Support Services"
    assert c.solicitation_type == "o"
    assert c.set_aside_code == "SDVOSBC"
    assert c.set_aside_label == "SDVOSB Competitive"
    assert c.naics_code == "541512"
    assert c.agency == "Department of Defense"
    assert c.place_of_performance == "Fort Bragg, NC"
    assert c.contact is not None
    assert c.contact.name == "Jane Smith"
    assert c.contact.email == "jane@army.mil"


def test_parse_award_opportunity():
    c = _parse_opportunity(AWARD_OPPORTUNITY)
    assert c is not None
    assert c.solicitation_type == "a"
    assert c.solicitation_type_label == "Award Notice"


def test_parse_missing_fields():
    """Minimal record — only required field is noticeId."""
    c = _parse_opportunity({"noticeId": "xyz"})
    assert c is not None
    assert c.notice_id == "xyz"
    assert c.title == "Untitled"
    assert c.agency is None
    assert c.contact is None


def test_parse_null_fields():
    """SAM.gov sometimes sends explicit nulls."""
    c = _parse_opportunity({
        "noticeId": None,
        "title": None,
        "type": None,
        "placeOfPerformance": None,
        "pointOfContact": None,
        "award": None,
    })
    assert c is not None
    assert c.notice_id == ""
    assert c.title == "Untitled"
    assert c.place_of_performance is None


def test_parse_bad_award_amount():
    opp = {**SAMPLE_OPPORTUNITY, "award": {"amount": "not-a-number"}}
    c = _parse_opportunity(opp)
    assert c is not None
    assert c.award_amount is None


def test_parse_string_total():
    """totalRecords sometimes comes back as a string from SAM.gov."""
    from models.contract import ContractSearchResult
    result = ContractSearchResult(total="1234", limit=25, offset=0, contracts=[])
    assert result.total == 1234


def test_parse_contact_list():
    contacts = [{"fullName": "Alice", "email": "a@b.com"}, {"fullName": "Bob"}]
    c = _parse_contact(contacts)
    assert c.name == "Alice"


def test_parse_contact_empty():
    assert _parse_contact(None) is None
    assert _parse_contact([]) is None
    assert _parse_contact({}) is None
