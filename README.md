# Automate IMGT V-QUEST usage on imgt.org

[![vquest](https://circleci.com/gh/ressy/vquest.svg?style=shield)](https://circleci.com/gh/ressy/vquest)

[IMGT](http://imgt.org)'s [V-QUEST](http://www.imgt.org/IMGT_vquest/analysis)
is only available via a web interface.  This Python package automates V-QUEST
usage by submitting request data like the web form does.  Curently only the
"Download AIRR formatted results" option is supported.

Example command-line usage, with rhesus sequences in seqs.fasta:

    pip install . # or skip this and use "python -m vquest" below
    vquest --species rhesus-monkey --receptorOrLocusType IG --fileSequences seqs.fasta

The output is saved to `Parameters.txt` and `vquest_airr.tsv` (the files
V-QUEST provides in a zip archive) in the working directory.

Or with `--align` to automatically extract the alignment as FASTA:

    vquest --align --species rhesus-monkey --receptorOrLocusType IG --fileSequences seqs.fasta

Here the aligned FASTA text is printed directly to standard output.

Example Python usage:

    >>> from vquest import *
    >>> config = layer_configs(DEFAULTS, {"species": "rhesus-monkey", "receptorOrLocusType": "IG", "fileSequences": "seqs.fasta"})
    >>> result = vquest(config)
    >>> result.keys()
    dict_keys(['Parameters.txt', 'vquest_airr.tsv'])

Here the output is a dictionary of filenames to contents.

The only required options are species, receptorOrLocusType, and either
fileSequences or sequences (to provide sequences directly as text).  Options
can be given via command-line arguemnts or one or more YAML configuration
files.  See [data/defaults.yml](data/defaults.yml) and `./vquest.py --help` for
details.

The web form will only accept 50 sequences at a time, so the sequences given
here are grouped into chunks of 50, submitted, and the results combined.  A
delay (default 1 second) is used between submissions to avoid being impolite to
the server.

 * V-QUEST: <http://www.imgt.org/IMGT_vquest/analysis>
 * V-QUEST docs: <http://www.imgt.org/IMGT_vquest/user_guide#intro>
 * A different approach, using [Selenium](https://www.selenium.dev/) to automate V-QUEST usage with a browser: <https://github.com/AndrewZoldy/IMGT_VQUEST_BOT>
