from datetime import date, timedelta

from wxdecide.database.seed import _missing_ranges

BUFFER = timedelta(days=7)


def test_missing_ranges_full_window_when_nothing_stored():
    ranges = _missing_ranges(None, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == [(date(2021, 1, 1), date(2026, 1, 1))]


def test_missing_ranges_empty_when_fully_covered():
    existing = (date(2021, 1, 1), date(2026, 1, 1))

    ranges = _missing_ranges(existing, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == []


def test_missing_ranges_head_gap_when_target_starts_earlier():
    existing = (date(2025, 1, 1), date(2026, 1, 1))

    ranges = _missing_ranges(existing, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == [(date(2021, 1, 1), date(2025, 1, 1) + BUFFER)]


def test_missing_ranges_tail_gap_when_target_ends_later():
    existing = (date(2021, 1, 1), date(2023, 1, 1))

    ranges = _missing_ranges(existing, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == [(date(2023, 1, 1) - BUFFER, date(2026, 1, 1))]


def test_missing_ranges_both_gaps_when_existing_is_a_narrow_middle_slice():
    existing = (date(2023, 1, 1), date(2023, 6, 1))

    ranges = _missing_ranges(existing, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == [
        (date(2021, 1, 1), date(2023, 1, 1) + BUFFER),
        (date(2023, 6, 1) - BUFFER, date(2026, 1, 1)),
    ]


def test_missing_ranges_head_clamped_to_end_date_if_buffer_overshoots():
    existing = (date(2025, 12, 30), date(2026, 1, 1))

    ranges = _missing_ranges(existing, date(2021, 1, 1), date(2026, 1, 1), BUFFER)

    assert ranges == [(date(2021, 1, 1), date(2026, 1, 1))]
