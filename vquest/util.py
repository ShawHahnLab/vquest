"""
Misc standalone utilities.
"""

from io import BytesIO
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
