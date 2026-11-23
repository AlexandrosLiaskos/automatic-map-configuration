# Changelog

All notable changes to this library are recorded in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `propose(columns, record_count, options)`: the first map configuration of a dataset, meaning the title, the field of
  the colours, the filters, the charts, the shown fields and clustering, with the reasons for the title and the
  colours.
- `profile(records, columns)`: the kind, counts, range, most frequent values and suggested filter of every column of a
  table of records.
- `numbers_the_records` and `is_hidden_by_default`, the two column tests that the proposal uses.
- Column names and headers read in English and Greek, without case or accents; thresholds as `ProposalOptions`.
