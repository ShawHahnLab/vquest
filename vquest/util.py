"""
Misc standalone utilities.
"""

import csv
from io import BytesIO, StringIO
from zipfile import ZipFile

def chunker(iterator, chunksize):
    """Iterate over another iterator in fixed-size chunks.

    This gives a list for each chunk (not another iterator) so it puts each
    chunk in memory at once.
    """
    # inspired by https://stackoverflow.com/a/8991553/4499968
    chunk = []
    try:
        for item in iterator:
            chunk.append(item)
            if len(chunk) == chunksize:
                yield chunk
                chunk = []
    except StopIteration:
        pass
    yield chunk

def unzip(txt):
    """Extract .zip data from bytes into dict keyed on filenames."""
    with BytesIO(txt) as f_in:
        zipobj = ZipFile(f_in)
        zipdata = {}
        for item in zipobj.infolist():
            with zipobj.open(item) as stream:
                zipdata[item.filename] = stream.read()
    return zipdata

def airr_to_fasta(
        airr_txt,
        seqid_col="sequence_id", aln_col="sequence_alignment", fallback_col="sequence"):
    """Convert AIRR TSV table to FASTA, both as strings.

    If the alignment column is empty for a given row, the sequence will be
    taken from fallback_col, if provided.
    """
    reader = csv.DictReader(StringIO(airr_txt), delimiter="\t")
    fasta = ""
    for row in reader:
        seq = row[aln_col]
        if fallback_col:
            seq = seq or row[fallback_col]
        fasta += ">%s\n%s\n" % (row[seqid_col], seq)
    return fasta

class VquestError(Exception):
    """Vquest-related errors.  These can have one or more messages provided by the server."""

    def __init__(self, message, server_messages=None):
        self.message = message
        self.server_messages = server_messages
        super().__init__(self.message)
