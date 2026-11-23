"""Automatic Map Configuration from Attribute Profiles.

Proposes the first map configuration of a dataset (the title of each record, the field of the colours, the filters,
the charts, the fields shown for a record, clustering) from the profiles of its columns.

Copyright (C) 2026 Alexandros Liaskos
SPDX-License-Identifier: AGPL-3.0-only
"""

from .profiles import profile
from .proposal import (
    ColumnProfile,
    MapConfiguration,
    ProposalOptions,
    is_hidden_by_default,
    numbers_the_records,
    propose,
)

__all__ = [
    "ColumnProfile",
    "MapConfiguration",
    "ProposalOptions",
    "is_hidden_by_default",
    "numbers_the_records",
    "profile",
    "propose",
]
__version__ = "0.1.0"
