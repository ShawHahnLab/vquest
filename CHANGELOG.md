# Changelog

## 0.0.5 - 2021-03-03

### Added

 * `--align` argument (via `airr_to_fasta` function) for exraction of sequence
   alignment FASTA from AIRR results ([#1])
 * Error messages sent by the server are now raised as an exception containing
   the server-provided message(s) ([#7])

### Changed

 * Reorganized and expanded test code as its own package ([#6])
 * Added basic test of command-line usage ([#10])
 * Clarified wording on required options ([#8])

### Fixed

 * Parse command-line options that should be integers from a finite list of
   options as integers instead of strings ([#5])

[#10]: https://github.com/ressy/vquest/pull/10
[#8]: https://github.com/ressy/vquest/pull/8
[#7]: https://github.com/ressy/vquest/pull/7
[#6]: https://github.com/ressy/vquest/pull/6
[#5]: https://github.com/ressy/vquest/pull/5
[#1]: https://github.com/ressy/vquest/pull/1
