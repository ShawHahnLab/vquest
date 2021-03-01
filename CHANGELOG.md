# Changelog

## dev

### Added

 * `--align` argument (via `airr_to_fasta` function) for exraction of sequence
   alignment FASTA from AIRR results ([#1])

### Changed

 * Reorganized and expanded test code as its own package ([#6])

### Fixed

 * Parse command-line options that should be integers from a finite list of
   options as integers instead of strings ([#5])

[#6]: https://github.com/ressy/vquest/pull/6
[#5]: https://github.com/ressy/vquest/pull/5
[#1]: https://github.com/ressy/vquest/pull/1
