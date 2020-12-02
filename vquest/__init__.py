"""
IMGT V-QUEST requests via imgt.org.

http://www.imgt.org/IMGT_vquest/analysis
"""

import sys
import logging
import time
from io import StringIO, BytesIO
from pathlib import Path
import yaml
import requests
from Bio import SeqIO
from .util import unzip, chunker

URL = "http://www.imgt.org/IMGT_vquest/analysis"
DELAY = 1 # for rate-limiting multiple requests
CHUNK_SIZE = 50 # to stay within V-QUEST's limit on sequences in one go
LOGGER = logging.getLogger(__name__)
LOGGER.propagate = False
LOGGER.addHandler(logging.StreamHandler())

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

def vquest(config):
    """Submit a request to V-QUEST"""
    if not all([
        config.get("species"),
        config.get("receptorOrLocusType"),
        config.get("fileSequences") or config.get("sequences")]):
        raise ValueError(
            "species, receptorOrLocusType, and fileSequences "
            "and/or sequences are required options")
    # species, receptorOrLocusType, and either fileSequences or sequences
    supported = [("resultType", "excel"), ("xv_outputtype", 3)]
    if all([config.get(pair[0]) == pair[1] for pair in supported]):
        output = {}
        records = _parse_records(config)
        if not records:
            raise ValueError("No sequences supplied")
        LOGGER.info("Starting request batch for %d sequences total", len(records))
        for chunk in chunker(records, CHUNK_SIZE):
            if output:
                time.sleep(DELAY)
            LOGGER.info("Sending request with %d sequences...", len(chunk))
            out_handle = StringIO()
            SeqIO.write(chunk, out_handle, "fasta")
            config_chunk = config.copy()
            config_chunk["sequences"] = out_handle.getvalue()
            config_chunk["inputType"] = "inline"
            response = requests.post(URL, data = config_chunk)
            response = unzip(response.content)
            # Only keep one copy of the Parameters.txt data, but append rows
            # (minus header) of vquest_airr.tsv together
            if "Parameters.txt" not in output:
                output["Parameters.txt"] = response["Parameters.txt"].decode()
            if "vquest_airr.tsv" not in output:
                output["vquest_airr.tsv"] = response["vquest_airr.tsv"].decode()
            else:
                airr = response["vquest_airr.tsv"].decode()
                output["vquest_airr.tsv"] += "\n".join(airr.splitlines()[1:])
        return output
    needed = " ".join([pair[0] + "=" + str(pair[1]) for pair in supported])
    observed = " ".join([pair[0] + "=" + str(config.get(pair[0])) for pair in supported])
    raise NotImplementedError(("Only " + needed + " currently supported, not " + observed))

def load_config(path):
    """Load YAML config file."""
    LOGGER.debug("Loading config file: %s", path)
    with open(path) as f_in:
        config = yaml.load(f_in, Loader=yaml.SafeLoader)
    return config

def layer_configs(*configs):
    """Merge dictionaries one after the other.

    The result is a shallow copy of the pairs in each input dictionary.
    """
    config_full = configs[0].copy()
    for config in configs[1:]:
        config_full.update(config)
    return config_full

def __load_options():
    data = load_config(Path(__file__).parent / "data" / "options.yml")
    mapping = {"int": int, "bool": bool, "str": str}
    for opt_section in data:
        for val in opt_section["options"].values():
            try:
                val["values"] = mapping.get(val["values"], val["values"])
            except TypeError:
                pass
    return data

def __load_default_config():
    return load_config(Path(__file__).parent / "data" / "defaults.yml")

DEFAULTS = __load_default_config()
OPTIONS = __load_options()
