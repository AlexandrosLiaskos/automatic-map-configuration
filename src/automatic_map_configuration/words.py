"""The words that tell the role of a column, in English and Greek, compared without case or accents.

A column is recognised by its name and by its label (the header as the data gave it), so that a Greek header such as
"Α/Α" or "Όνομα" is understood even when the name of the column has been reduced to Latin letters.
"""

from __future__ import annotations

import re
import unicodedata

# Words that name a column holding the title of each record. A title column is one of these words alone, or followed by
# a short language suffix ("name_en", "name_gr").
TITLE_WORDS = (
    "name",
    "title",
    "site",
    "label",
    "place",
    "locality",
    "toponym",
    "ονομα",
    "ονομασια",
    "τιτλος",
    "τοποθεσια",
    "τοπωνυμιο",
)

# Words that name a column which only numbers the records.
NUMBERING_WORDS = frozenset(
    {
        "id",
        "no",
        "nr",
        "num",
        "number",
        "code",
        "fid",
        "gid",
        "oid",
        "objectid",
        "aa",
        "serial",
        "αα",
        "αρ",
        "αριθμος",
        "κωδ",
        "κωδικος",
    }
)

# Columns that hold coordinates or bookkeeping of the source, and are not shown or offered by default.
COORDINATE_NAMES = frozenset(
    {
        "longitude",
        "lon",
        "lng",
        "long",
        "x",
        "centroid_lng",
        "easting",
        "x_coord",
        "xcoord",
        "latitude",
        "lat",
        "y",
        "centroid_lat",
        "northing",
        "y_coord",
        "ycoord",
        "γεωγραφικο_μηκος",
        "γεωγραφικο_πλατος",
    }
)
BOOKKEEPING_NAMES = frozenset({"id", "fid", "created_at", "updated_at"})


def normalise(text: str) -> str:
    """Lower case without accents: "Όνομα" becomes "ονομα"."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def words_of(text: str) -> list[str]:
    """The words of a name or label, without case or accents: "Record No." gives ["record", "no"]."""
    return [word for word in re.split(r"[^\w]+|_", normalise(text)) if word]


def joined(text: str) -> str:
    """A name or label as words joined by underscores: "Created at" gives "created_at"."""
    return "_".join(words_of(text))


def compact(text: str) -> str:
    """A name or label with only its letters and digits: "Α/Α" gives "αα"."""
    return "".join(words_of(text))


# The lists are compared in the same form as the names: without case or accents, and with every sigma as σ, since
# casefold() turns the final ς into σ ("μήκος" becomes "μηκοσ").
TITLE_WORDS = tuple(normalise(word) for word in TITLE_WORDS)
NUMBERING_WORDS = frozenset(normalise(word) for word in NUMBERING_WORDS)
COORDINATE_NAMES = frozenset(normalise(name) for name in COORDINATE_NAMES)
BOOKKEEPING_NAMES = frozenset(normalise(name) for name in BOOKKEEPING_NAMES)
