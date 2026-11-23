import csv
import datetime as dt
import io

from automatic_map_configuration import profile, propose

TABLE = """\
Α/Α,Όνομα,Τύπος,Βάθος (m),Ημερομηνία,Ενεργό,Κωδικός,longitude,latitude
1,Αλυκή,λιμνοθάλασσα,"1,5",2021-04-05,ναι,007,23.70,37.90
2,Κορισσίων,λιμνοθάλασσα,2,2021-05-01,όχι,008,19.90,39.40
3,Μεσολόγγι,λιμνοθάλασσα,"0,8",2022-02-30,ναι,009,21.40,38.35
4,Βιστωνίδα,λίμνη,,2023-07-15,ναι,010,25.10,41.05
5,Κεριού,λιμνοθάλασσα,"3,25",,όχι,011,20.80,37.65
"""


def by_name(profiles):
    return {p.name: p for p in profiles}


def test_kinds_counts_and_ranges_of_a_greek_table():
    found = by_name(profile(csv.DictReader(io.StringIO(TABLE))))
    assert found["Α/Α"].kind == "number" and (found["Α/Α"].minimum, found["Α/Α"].maximum) == (1.0, 5.0)
    assert found["Όνομα"].kind == "text" and found["Όνομα"].distinct == 5
    depth = found["Βάθος (m)"]
    assert (depth.kind, depth.filled, depth.minimum, depth.maximum) == ("number", 4, 0.8, 3.25)
    assert found["Ενεργό"].kind == "yes/no" and found["Ενεργό"].filter == "list"
    # A code with leading zeros stays text, and so does a column with an impossible date (30 February).
    assert found["Κωδικός"].kind == "text"
    assert found["Ημερομηνία"].kind == "text"
    assert found["Τύπος"].values == (("λιμνοθάλασσα", 4), ("λίμνη", 1))
    assert found["Τύπος"].filter == "list"


def test_dates_numbers_and_missing_values():
    rows = [
        {"day": "2021-04-05", "when": dt.date(2020, 1, 2), "count": 3, "note": None},
        {"day": "2021-04-06T10:30:00", "when": dt.datetime(2020, 1, 3, 8, 0), "count": 4.5, "note": " "},
    ]
    found = by_name(profile(rows))
    day = found["day"]
    assert (day.kind, day.minimum, day.maximum, day.filter) == ("date", "2021-04-05", "2021-04-06", "range")
    assert found["when"].kind == "date"
    assert (found["count"].kind, found["count"].mean) == ("number", 3.75)
    assert (found["note"].filled, found["note"].filter) == (0, None)


def test_a_number_with_many_values_gets_a_range_and_with_few_a_list():
    found = by_name(profile([{"many": i, "few": i % 3} for i in range(30)]))
    assert (found["many"].filter, found["few"].filter) == ("range", "list")


def test_a_table_of_records_gives_a_whole_proposal():
    rows = list(csv.DictReader(io.StringIO(TABLE)))
    found = propose(profile(rows), record_count=len(rows))
    assert found.title_column == "Όνομα"
    assert found.colour_by == "Τύπος"
    assert "Α/Α" not in dict(found.filters) and "Α/Α" not in found.charts
    assert "longitude" not in found.record_columns and "latitude" not in found.record_columns
