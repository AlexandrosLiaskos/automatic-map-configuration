# Automatic Map Configuration from Attribute Profiles

[![Checks](https://github.com/AlexandrosLiaskos/automatic-map-configuration/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandrosLiaskos/automatic-map-configuration/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/automatic-map-configuration.svg)](https://pypi.org/project/automatic-map-configuration/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24467041.svg)](https://doi.org/10.5281/zenodo.24467041)
[![Licence: AGPL-3.0](https://img.shields.io/badge/licence-AGPL--3.0-blue.svg)](LICENSE)

When a research dataset is turned into a web map, someone has to decide which column gives the title of each record,
which column colours the map, which columns visitors can filter by, which deserve a chart, and which are shown when a
record is opened. This library proposes those decisions from the columns of the dataset, so that a new map starts from
a sensible configuration instead of an empty one.

It works from **profiles** of the columns (kind, number of values, range), which it can compute from plain records,
and it understands column names and headers in **English and Greek**, with or without accents.

## Installation

```sh
pip install automatic-map-configuration
```

Python 3.10 or later; no dependencies.

## Use

With a file `lagoons.csv`:

```text
Α/Α,Όνομα,Τύπος,Έκταση (km²),longitude,latitude
1,Αλυκή Κίτρους,λιμνοθάλασσα,1.2,22.65,40.36
2,Κορισσίων,λιμνοθάλασσα,4.5,19.90,39.40
3,Μεσολογγίου,λιμνοθάλασσα,150,21.40,38.35
4,Βιστωνίδα,λίμνη,45,25.10,41.05
```

```python
import csv
from automatic_map_configuration import profile, propose

with open("lagoons.csv", encoding="utf-8") as file:
    records = list(csv.DictReader(file))

configuration = propose(profile(records), record_count=len(records))
print(configuration.to_dict())
```

```python
{
    "title_column": "Όνομα",
    "colour_by": "Τύπος",
    "filters": [{"column": "Τύπος", "type": "list"}, {"column": "Έκταση (km²)", "type": "list"}],
    "charts": [],
    "record_columns": ["Α/Α", "Όνομα", "Τύπος", "Έκταση (km²)"],
    "cluster": False,
}
```

The record number `Α/Α` is shown with each record but offered neither as a filter nor as a chart. The coordinates are
hidden. With four records, the area gets a list filter and no chart; with more than ten values it would get a range
and a chart.

`configuration.reasons` tells which rule chose the title and the colours.

If you already have profiles, from a database for example, pass them as `ColumnProfile` objects or as mappings with
the keys `name`, `label`, `kind`, `filled`, `distinct`, `filter`, `min`, `max`, `mean` and `values`. `name` is the
column's name; `label` is the header as the data gave it. Both are read, so a Greek header is understood even when the
column's name has been reduced to Latin letters.

## The rules

| Decision             | Rule                                                                                                                                                                                                                                                                                                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Title of each record | A text column named as a title ("name", "title", "site", "label", "place", "Όνομα", "Ονομασία", "Τίτλος", "Τοποθεσία", alone or with a language code such as `name_en`; a title word alone comes first, then the preferred language, English by default, then other languages). Otherwise the first text column whose values differ in at least 80 % of the records. Otherwise the first column. |
| Field of the colours | The first column, other than the title, with a list filter, 2 to 8 values, a value in at least half of the records, that does not number the records and does not differ in every record.                                                                                                                                                                                                        |
| Filters              | Every column with a filter, other than the title and a record number; at most six.                                                                                                                                                                                                                                                                                                               |
| Charts               | Every number column with more than ten values that does not number the records; at most three.                                                                                                                                                                                                                                                                                                   |
| Shown fields         | Every column except coordinates (`longitude`, `lat`, `x`, `easting`, "Γεωγραφικό μήκος", …) and bookkeeping (`id`, `created_at`, …).                                                                                                                                                                                                                                                             |
| Clustering           | For more than 100 records.                                                                                                                                                                                                                                                                                                                                                                       |

A column **numbers the records** when it has a different whole number in every record that has a value, has a value
in at least 90 % of the records, and its name or label says so ("id", "no", "nr", "code", "Α/Α", "Αριθμός",
"Κωδικός"). The name is part of the rule on purpose: a table with one record per year also has a different whole
number in every record, and there the range of years is a useful filter.

Every threshold is an option of `ProposalOptions`: `title_uniqueness`, `colour_min_values`, `colour_max_values`,
`colour_min_filled`, `numbering_min_filled`, `chart_min_distinct`, `max_filters`, `max_charts`, `cluster_above` and
`title_language`.

### Profiles

`profile(records, columns=None)` reads an iterable of mappings, such as the rows of `csv.DictReader` or the
properties of GeoJSON features. For every column it gives:

- **Kind.** A column is a number when every value is one, with a point or a comma as the decimal mark. A value with a
  leading zero, such as `007`, is a code, not a number. A column is a date when every value is a valid ISO date (a time
  is allowed); an impossible date such as 30 February makes it text. It is yes/no when every value is a boolean or
  yes/no, true/false, ναι/όχι. Anything else is text.
- **Counts.** The number of records with a value and the number of different values.
- **Range.** For numbers, the minimum, maximum and mean; for dates, the first and last day.
- **Values.** The 60 most frequent values, with their counts.
- **Suggested filter.** A range for dates and for numbers with more than ten values; a list for other numbers, for
  yes/no, and for text with 2 to 60 values; none for other text.

## Origin

The rules come from the WebGIS Builder of the National and Kapodistrian University of Athens. They were made
independent of it, and they now also read headers in Greek and detect a record number with a few empty values.

## Citation

Liaskos, A. (2026). _Automatic Map Configuration from Attribute Profiles_ (Version 0.1.0) [Computer software]. Zenodo.
https://doi.org/10.5281/zenodo.24467041

To cite every version at once, use the concept DOI [10.5281/zenodo.24467040](https://doi.org/10.5281/zenodo.24467040),
which always resolves to the latest release. The citation is also given in [CITATION.cff](CITATION.cff), which GitHub
offers under "Cite this repository". Each release is archived on Zenodo with its own DOI.

## Licence

Copyright © 2026 Alexandros Liaskos, National and Kapodistrian University of Athens.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General
Public License, version 3, as published by the Free Software Foundation ([LICENSE](LICENSE)). It is distributed in the
hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness
for a particular purpose.
