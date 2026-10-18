import pytest
from pydantic import ValidationError

from seshat.contract import parse_event

VALID = (
    '{"type":"detector","device_id":"det-01","ts":1729100000,'
    '"kind":"gamma","counts":47,"interval_s":10}'
)


def test_valid_event_parses():
    event = parse_event(VALID)
    assert event.device_id == "det-01"
    assert event.counts == 47


def test_rate_is_counts_per_second():
    assert parse_event(VALID).rate_cps == pytest.approx(4.7)


def test_negative_counts_rejected():
    with pytest.raises(ValidationError):
        parse_event(VALID.replace('"counts":47', '"counts":-1'))


def test_zero_interval_rejected():
    with pytest.raises(ValidationError):
        parse_event(VALID.replace('"interval_s":10', '"interval_s":0'))


def test_unknown_kind_rejected():
    with pytest.raises(ValidationError):
        parse_event(VALID.replace("gamma", "alpha"))


def test_missing_field_rejected():
    with pytest.raises(ValidationError):
        parse_event('{"type":"detector","device_id":"det-01","ts":1}')


def test_counts_as_string_rejected():
    with pytest.raises(ValidationError):
        parse_event(VALID.replace('"counts":47', '"counts":"47"'))


def test_malformed_json_rejected():
    with pytest.raises(ValidationError):
        parse_event("not json at all")