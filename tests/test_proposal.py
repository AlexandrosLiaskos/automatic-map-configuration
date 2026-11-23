from automatic_map_configuration import ColumnProfile, ProposalOptions, is_hidden_by_default, numbers_the_records, propose


def column(name, kind, distinct, filled, label=None, **more):
    return ColumnProfile(name=name, label=label or name, kind=kind, distinct=distinct, filled=filled, **more)


def test_the_title_and_the_record_number_are_left_out_of_the_filters():
    # The record number has a gap (0 to 21 for 20 records), as in a real table of beachrocks.
    found = propose(
        [
            column("record_no", "number", 20, 20, minimum=0.0, maximum=21.0, filter="range"),
            column("name", "text", 20, 20, filter="list"),
            column("type", "text", 3, 20, filter="list"),
            column("area_km2", "number", 20, 20, minimum=0.4, maximum=310.0, filter="range"),
        ],
        record_count=20,
    )
    assert found.title_column == "name"
    assert found.colour_by == "type"
    assert found.filters == (("type", "list"), ("area_km2", "range"))
    assert found.charts == ("area_km2",)
    assert found.record_columns == ("record_no", "name", "type", "area_km2")
    assert found.cluster is False


def test_one_record_per_year_keeps_the_filter_of_years():
    found = propose(
        [column("year", "number", 20, 20, minimum=2001.0, maximum=2020.0, filter="range"), column("place", "text", 20, 20)],
        record_count=20,
    )
    assert found.filters == (("year", "range"),)
    assert found.charts == ("year",)


def test_greek_headers_are_understood_through_their_labels():
    found = propose(
        [
            column("column", "number", 12, 12, label="Α/Α", minimum=1, maximum=12, filter="range"),
            column("column_2", "text", 12, 12, label="Όνομα"),
            column("column_3", "text", 4, 12, label="Τύπος", filter="list"),
            column("column_4", "number", 12, 12, label="Γεωγραφικό μήκος", minimum=20.1, maximum=26.9, filter="range"),
        ],
        record_count=12,
    )
    assert found.title_column == "column_2"
    assert found.colour_by == "column_3"
    assert found.filters == (("column_3", "list"),)
    assert found.record_columns == ("column", "column_2", "column_3")


def test_a_record_number_with_a_few_empty_values_still_numbers_the_records():
    number = column("no", "number", 39, 39, minimum=1, maximum=40, filter="range")
    assert numbers_the_records(number, 40)
    assert not numbers_the_records(column("no", "number", 20, 20, minimum=1, maximum=40), 40)  # half empty: not a numbering
    assert not numbers_the_records(column("depth_m", "number", 40, 40, minimum=1, maximum=40), 40)  # no word for it


def test_greek_words_with_a_final_sigma_are_recognised():
    assert numbers_the_records(column("column", "number", 9, 9, label="Αριθμός", minimum=1, maximum=9), 9)
    assert numbers_the_records(column("column", "number", 9, 9, label="ΚΩΔΙΚΟΣ", minimum=1, maximum=9), 9)
    titled = propose([column("kind", "text", 3, 30), column("column", "text", 30, 30, label="Τίτλος")], record_count=30)
    assert titled.title_column == "column"


def test_a_record_number_or_a_value_of_every_record_never_colours_the_map():
    found = propose(
        [
            column("title", "text", 6, 6),
            column("code", "number", 6, 6, minimum=1, maximum=6, filter="list"),
            column("label_2", "text", 6, 6, filter="list"),
            column("kind", "text", 2, 6, filter="list"),
        ],
        record_count=6,
    )
    assert found.colour_by == "kind"


def test_coordinates_and_bookkeeping_are_hidden_by_their_name_or_label():
    assert is_hidden_by_default(column("lon", "number", 5, 5))
    assert is_hidden_by_default(column("column_7", "number", 5, 5, label="Latitude"))
    assert is_hidden_by_default(column("created_at", "date", 5, 5))
    assert not is_hidden_by_default(column("depth", "number", 5, 5))


def test_a_title_word_with_a_language_code_is_a_title_but_with_other_endings_it_is_not():
    with_code = propose([column("kind", "text", 3, 30), column("name_en", "text", 30, 30)], record_count=30)
    assert with_code.title_column == "name_en"
    assert with_code.reasons["title_column"] == "its name says it is the title"
    other = propose([column("site_type", "text", 3, 30), column("place_name", "text", 30, 30)], record_count=30)
    assert other.title_column == "place_name"
    assert other.reasons["title_column"] == "its values differ in nearly every record"


def test_a_title_in_the_preferred_language_comes_before_other_languages():
    columns = [column("name_gr", "text", 30, 30), column("name_en", "text", 30, 30)]
    assert propose(columns, record_count=30).title_column == "name_en"
    assert propose(columns, record_count=30, options=ProposalOptions(title_language="gr")).title_column == "name_gr"
    assert propose([*columns, column("title", "text", 30, 30)], record_count=30).title_column == "title"


def test_the_thresholds_are_options():
    columns = [column("name", "text", 150, 150)] + [
        column(f"value_{i}", "number", 50, 150, minimum=0.5, maximum=99.5, filter="range") for i in range(8)
    ]
    found = propose(columns, record_count=150)
    assert (len(found.filters), len(found.charts), found.cluster) == (6, 3, True)
    narrow = propose(columns, record_count=150, options=ProposalOptions(max_filters=2, max_charts=1, cluster_above=500))
    assert (len(narrow.filters), len(narrow.charts), narrow.cluster) == (2, 1, False)


def test_profiles_may_be_given_as_mappings_and_the_result_as_plain_data():
    found = propose(
        [
            {"name": "name", "label": "Name", "kind": "text", "distinct": 3, "filled": 3, "filter": None},
            {"name": "type", "label": "Type", "kind": "text", "distinct": 2, "filled": 3, "filter": "list", "values": [["a", 2], ["b", 1]]},
        ],
        record_count=3,
    )
    assert found.to_dict() == {
        "title_column": "name",
        "colour_by": "type",
        "filters": [{"column": "type", "type": "list"}],
        "charts": [],
        "record_columns": ["name", "type"],
        "cluster": False,
    }


def test_a_dataset_without_columns_has_no_title():
    found = propose([], record_count=0)
    assert (found.title_column, found.colour_by, found.filters, found.record_columns) == (None, None, (), ())
