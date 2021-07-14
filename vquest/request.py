"""
Send requests to the IMGT/V-QUEST server.
"""

import time
import logging
from io import StringIO
import requests
from requests_html import HTML
from Bio import SeqIO
from .util import unzip, chunker, VquestError

LOGGER = logging.getLogger(__name__)

URL = "http://www.imgt.org/IMGT_vquest/analysis"
DELAY = 1 # for rate-limiting multiple requests
CHUNK_SIZE = 50 # to stay within V-QUEST's limit on sequences in one go

def _parse_records(config):
    """Extract Seq records for sequences given in config"""
    records = []
    if "sequences" in config and config["sequences"]:
        with StringIO(config["sequences"]) as seqs_stream:
            records.extend(list(SeqIO.parse(seqs_stream, "fasta")))
    if "fileSequences" in config and config["fileSequences"]:
        with open(config["fileSequences"]) as f_in:
            records.extend(list(SeqIO.parse(f_in, "fasta")))
    return records

def vquest(config, collapse=True):
    """Submit a request to V-QUEST.

    config should be a dictionary key/value pairs to use in the request.  See
    data/options.yml for a full list, organized into sections.  Currently
    resultType must be "excel" and xv_outputtype must be 3 (for "Download AIRR
    formatted results").

    sequences are batched into sets of 50 (the most allowed by V-QUEST) and
    submitted one batch at a time.  If collapse is True, results are combined
    as though they were submitted and processed as a single request, and a
    dictionary of file names to text contents is returned.  If collapse is
    False, a list of dictionaries is returned, one for each batch, storing raw
    byte contents.
    """
    if not all([
        config.get("species"),
        config.get("receptorOrLocusType"),
        config.get("fileSequences") or config.get("sequences")]):
        raise ValueError(
            "species, receptorOrLocusType, and fileSequences "
            "and/or sequences are required options")
    supported = [("resultType", "excel"), ("xv_outputtype", 3)]
    if all([config.get(pair[0]) == pair[1] for pair in supported]):
        outputs = []
        records = _parse_records(config)
        if not records:
            raise ValueError("No sequences supplied")
        LOGGER.info("Starting request batch for %d sequences total", len(records))
        for chunk in chunker(records, CHUNK_SIZE):
            if outputs:
                time.sleep(DELAY)
            LOGGER.info("Sending request with %d sequences...", len(chunk))
            out_handle = StringIO()
            SeqIO.write(chunk, out_handle, "fasta")
            config_chunk = config.copy()
            config_chunk["sequences"] = out_handle.getvalue()
            config_chunk["inputType"] = "inline"
            response = requests.post(URL, data = config_chunk)
            ctype = response.headers.get("Content-Type")
            LOGGER.debug("Received data of type %s", ctype)
            if ctype and "text/html" in ctype:
                html = HTML(html=response.content)
                errors = [div.text for div in html.find("div.form_error")]
                if errors:
                    raise VquestError("; ".join(errors), errors)
            outputs.append(unzip(response.content))
        if not collapse:
            return outputs
        return _collapse_outputs(outputs)
    needed = " ".join([pair[0] + "=" + str(pair[1]) for pair in supported])
    observed = " ".join([pair[0] + "=" + str(config.get(pair[0])) for pair in supported])
    raise NotImplementedError(("Only " + needed + " currently supported, not " + observed))

def _collapse_outputs(outputs):
    """Combine batched output dictionaries into one."""
    output = {}
    for output_chunk in outputs:
        # Only keep one copy of the Parameters.txt data, but append rows
        # (minus header) of vquest_airr.tsv together
        if "Parameters.txt" not in output:
            output["Parameters.txt"] = output_chunk["Parameters.txt"].decode()
        if "vquest_airr.tsv" not in output:
            output["vquest_airr.tsv"] = output_chunk["vquest_airr.tsv"].decode()
        else:
            airr = output_chunk["vquest_airr.tsv"].decode()
            output["vquest_airr.tsv"] += "\n".join(airr.splitlines()[1:])
    return output
