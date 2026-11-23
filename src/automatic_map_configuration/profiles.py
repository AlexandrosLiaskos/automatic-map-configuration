"""Profiles of the columns of a table of records: kind, counts, range and most frequent values."""

from __future__ import annotations

import datetime as dt
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .proposal import ColumnProfile, Kind
from .words import normalise

# A number written as text: an optional sign, digits, an optional decimal part with a point or a comma, an optional
# exponent. A number with a leading zero ("007") is a code, not a number.
_NUMBER = re.compile(r"^[+-]?(?:0|[1-9]\d*)(?:[.,]\d+)?(?:[eE][+-]?\d+)?$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$")
_YES = {"true", "yes", "y", "ναι"}
_NO = {"false", "no", "n", "οχι"}  # compared after normalise(), which keeps these as they are

#: A text column with more than this many different values gets no list filter.
LIST_MAX_VALUES = 60
#: A number column with more than this many different values gets a range filter instead of a list.
RANGE_MIN_VALUES = 10


def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, float) and math.isnan(value))


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str) and _NUMBER.match(value.strip()):
        parsed = float(value.strip().replace(",", "."))
        return parsed if math.isfinite(parsed) else None
    return None


def _date(value: Any) -> str | None:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str) and _DATE.match(value.strip()):
        try:
            return dt.date.fromisoformat(value.strip()[:10]).isoformat()
        except ValueError:  # 2023-02-30 and the like are text, not dates
            return None
    return None


def _yes_no(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        word = normalise(value.strip())
        if word in _YES:
            return True
        if word in _NO:
            return False
    return None


def _kind(values: Sequence[Any]) -> Kind:
    """The kind that every filled value of a column has: yes/no, number, date or, failing these, text."""
    if values and all(_yes_no(v) is not None for v in values) and not all(_number(v) is not None for v in values):
        return "yes/no"
    if values and all(_number(v) is not None for v in values):
        return "number"
    if values and all(_date(v) is not None for v in values):
        return "date"
    return "text"


def _shown(value: Any, kind: Kind) -> str:
    if kind == "number":
        number = _number(value)
        return str(int(number)) if number is not None and number.is_integer() else str(number)
    if kind == "date":
        return _date(value) or str(value)
    if kind == "yes/no":
        return "yes" if _yes_no(value) else "no"
    return str(value).strip()


def profile(records: Iterable[Mapping[str, Any]], columns: Sequence[str] | None = None) -> list[ColumnProfile]:
    """The profile of every column of a table of records (an iterable of mappings, as from `csv.DictReader` or the
    properties of GeoJSON features). `columns` gives the columns and their order; by default, every key in the order
    first met.

    Empty strings and None are missing values. A column is a number when every value is one, with a point or a comma as
    the decimal mark; a date when every value is a valid ISO date (a time is allowed); yes/no when every value is a
    boolean or yes/no, true/false, ναι/όχι; otherwise text.
    """
    rows = list(records)
    names = list(columns) if columns is not None else list(dict.fromkeys(key for row in rows for key in row))
    profiles = []
    for name in names:
        filled = [row.get(name) for row in rows if not _empty(row.get(name))]
        kind = _kind(filled)
        counts = Counter(_shown(value, kind) for value in filled)
        common = tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:LIST_MAX_VALUES])
        minimum = maximum = mean = None
        if kind == "number":
            numbers = [n for n in (_number(v) for v in filled) if n is not None]
            minimum, maximum, mean = min(numbers), max(numbers), sum(numbers) / len(numbers)
            suggested = "range" if len(counts) > RANGE_MIN_VALUES else "list"
        elif kind == "date":
            days = sorted(d for d in (_date(v) for v in filled) if d)
            minimum, maximum = days[0], days[-1]
            suggested = "range"
        elif kind == "yes/no":
            suggested = "list"
        else:
            suggested = "list" if 1 < len(counts) <= LIST_MAX_VALUES else None
        profiles.append(
            ColumnProfile(
                name=name,
                label=name,
                kind=kind,
                filled=len(filled),
                distinct=len(counts),
                filter=suggested if filled else None,
                minimum=minimum,
                maximum=maximum,
                mean=mean,
                values=common,
            )
        )
    return profiles
