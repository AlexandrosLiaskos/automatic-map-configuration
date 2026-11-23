"""The first map configuration of a dataset, proposed from the profiles of its columns."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from .words import BOOKKEEPING_NAMES, COORDINATE_NAMES, NUMBERING_WORDS, TITLE_WORDS, compact, joined, words_of

Kind = Literal["number", "date", "yes/no", "text"]
FilterType = Literal["list", "range"]


@dataclass(frozen=True)
class ColumnProfile:
    """What is known of a column of a dataset.

    `name` is the name of the column, `label` the header as the data gave it (often the same). `kind` is "number",
    "date", "yes/no" or "text". `filled` is the number of records with a value, `distinct` the number of different
    values. `filter` is the filter that suits the column: "list" (pick values), "range" (low and high) or None.
    """

    name: str
    kind: Kind
    filled: int
    distinct: int
    label: str = ""
    filter: FilterType | None = None
    minimum: float | str | None = None
    maximum: float | str | None = None
    mean: float | None = None
    values: tuple[tuple[str, int], ...] = ()

    @classmethod
    def from_mapping(cls, column: Mapping[str, Any]) -> ColumnProfile:
        """A profile from a mapping with the keys name, label, kind, filled, distinct, filter, min, max, mean, values."""
        return cls(
            name=str(column["name"]),
            label=str(column.get("label") or column["name"]),
            kind=column["kind"],
            filled=int(column.get("filled") or 0),
            distinct=int(column.get("distinct") or 0),
            filter=column.get("filter"),
            minimum=column.get("min", column.get("minimum")),
            maximum=column.get("max", column.get("maximum")),
            mean=column.get("mean"),
            values=tuple((str(value), int(count)) for value, count in column.get("values") or ()),
        )


@dataclass(frozen=True)
class ProposalOptions:
    """The thresholds of the proposal. The defaults are those of the WebGIS Builder."""

    #: A text column whose values differ in at least this share of the records can be the title.
    title_uniqueness: float = 0.8
    #: The field of the colours has from this many ...
    colour_min_values: int = 2
    #: ... to this many different values,
    colour_max_values: int = 8
    #: and a value in at least this share of the records.
    colour_min_filled: float = 0.5
    #: A column that numbers the records has a value in at least this share of them.
    numbering_min_filled: float = 0.9
    #: A number column is offered as a chart when it has more than this many different values.
    chart_min_distinct: int = 10
    #: At most this many filters and charts are proposed.
    max_filters: int = 6
    max_charts: int = 3
    #: Point markers are grouped in clusters when the dataset has more than this many records.
    cluster_above: int = 100
    #: Among title columns in several languages ("name_en", "name_gr"), the one in this language is preferred.
    title_language: str = "en"


@dataclass(frozen=True)
class MapConfiguration:
    """A proposed map configuration: which column gives the title of each record, which colours the map, which are
    offered as filters and charts, which are shown in the details of a record, and whether markers are clustered."""

    title_column: str | None
    colour_by: str | None
    filters: tuple[tuple[str, FilterType], ...] = ()
    charts: tuple[str, ...] = ()
    record_columns: tuple[str, ...] = ()
    cluster: bool = False
    reasons: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """The configuration as plain data, for JSON."""
        return {
            "title_column": self.title_column,
            "colour_by": self.colour_by,
            "filters": [{"column": column, "type": kind} for column, kind in self.filters],
            "charts": list(self.charts),
            "record_columns": list(self.record_columns),
            "cluster": self.cluster,
        }


def _names(column: ColumnProfile) -> tuple[str, ...]:
    """The name and the label of a column, each as words joined by underscores."""
    return tuple(dict.fromkeys(joined(text) for text in (column.name, column.label or column.name) if text))


def is_hidden_by_default(column: ColumnProfile) -> bool:
    """True for a column of coordinates or of bookkeeping (id, created_at), which is not shown or offered by default."""
    return any(name in COORDINATE_NAMES or name in BOOKKEEPING_NAMES for name in _names(column))


def numbers_the_records(column: ColumnProfile, record_count: int, options: ProposalOptions | None = None) -> bool:
    """True for a column that only numbers the records: a different whole number for every record that has one, in
    nearly all records, and a name or label that says so ("id", "no", "code", "Α/Α", "Αριθμός").

    The name is part of the rule on purpose: a table with one record per year also has a different whole number for
    every record, and there the range of years is a useful filter.
    """
    options = options or ProposalOptions()
    if column.kind != "number" or record_count < 2 or column.filled < options.numbering_min_filled * record_count:
        return False
    if column.distinct != column.filled:
        return False
    low, high = column.minimum, column.maximum
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or low != int(low) or high != int(high):
        return False
    for text in (column.name, column.label or column.name):
        if set(words_of(text)) & NUMBERING_WORDS or compact(text) in NUMBERING_WORDS:
            return True
    return False


# Language codes that may follow a title word: "name_en", "name_gr", "ονομα_ελ".
LANGUAGE_SUFFIXES = frozenset({"en", "el", "gr", "ελ", "de", "fr", "it", "es", "pt", "nl", "tr"})  # no sigma among them


def _title_rank(column: ColumnProfile, language: str) -> int | None:
    """How well the name or label of a column says that it is the title: 0 for a title word alone ("name"), 1 with the
    preferred language code ("name_en"), 2 with another language code ("name_gr"), None when it does not."""
    ranks = []
    for name in _names(column):
        word, _, suffix = name.rpartition("_")
        if name in TITLE_WORDS:
            ranks.append(0)
        elif word in TITLE_WORDS and suffix in LANGUAGE_SUFFIXES:
            ranks.append(1 if suffix == language else 2)
    return min(ranks, default=None)


def propose(
    columns: Iterable[ColumnProfile | Mapping[str, Any]],
    record_count: int,
    options: ProposalOptions | None = None,
) -> MapConfiguration:
    """Proposes the first map configuration of a dataset from the profiles of its columns.

    - Title: a text column named as a title ("name", "title", "site", "Όνομα"), alone before one with the preferred
      language code ("name_en") before one with another ("name_gr"); else the first text column whose values differ
      in nearly every record; else the first column.
    - Colours: the first column, other than the title, with a list filter, 2 to 8 values, a value in at least half of
      the records, that does not number the records and does not differ in every record.
    - Filters: the columns with a filter, other than the title and a record number; at most six.
    - Charts: the number columns with more than ten values that do not number the records; at most three.
    - Details of a record: every column except coordinates and bookkeeping.
    - Clustering: for more than 100 records.

    `reasons` tells, for the title and the colours, which rule chose them.
    """
    options = options or ProposalOptions()
    profiles = [column if isinstance(column, ColumnProfile) else ColumnProfile.from_mapping(column) for column in columns]
    usable = [column for column in profiles if not is_hidden_by_default(column)]
    texts = [column for column in usable if column.kind == "text"]
    reasons: dict[str, str] = {}

    ranked = [
        (rank, index, column.name)
        for index, column in enumerate(texts)
        if (rank := _title_rank(column, options.title_language)) is not None
    ]
    title = min(ranked)[2] if ranked else None
    if title:
        reasons["title_column"] = "its name says it is the title"
    else:
        title = next((column.name for column in texts if column.distinct >= options.title_uniqueness * record_count), None)
        if title:
            reasons["title_column"] = "its values differ in nearly every record"
        elif usable:
            title = usable[0].name
            reasons["title_column"] = "the first column"

    numbering = {column.name for column in usable if numbers_the_records(column, record_count, options)}
    colour = next(
        (
            column.name
            for column in usable
            if column.name != title
            and column.name not in numbering
            and column.filter == "list"
            and options.colour_min_values <= column.distinct <= options.colour_max_values
            and column.distinct < max(column.filled, 1)
            and column.filled >= options.colour_min_filled * record_count
        ),
        None,
    )
    if colour:
        reasons["colour_by"] = "the first field with a few values that most records have"

    filters = tuple(
        (column.name, column.filter) for column in usable if column.filter and column.name != title and column.name not in numbering
    )[: options.max_filters]
    charts = tuple(
        column.name
        for column in usable
        if column.kind == "number" and column.distinct > options.chart_min_distinct and column.name not in numbering
    )[: options.max_charts]
    return MapConfiguration(
        title_column=title,
        colour_by=colour,
        filters=filters,
        charts=charts,
        record_columns=tuple(column.name for column in usable),
        cluster=record_count > options.cluster_above,
        reasons=reasons,
    )
