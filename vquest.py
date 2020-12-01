#!/usr/bin/env python

"""
IMGT V-QUEST requests via imgt.org.

http://www.imgt.org/IMGT_vquest/analysis
"""

import sys
import argparse
import logging
import time
from zipfile import ZipFile
from io import StringIO, BytesIO
from pathlib import Path
import yaml
import requests
from Bio import SeqIO

URL = "http://www.imgt.org/IMGT_vquest/analysis"
DELAY = 1 # for rate-limiting multiple requests
CHUNK_SIZE = 50 # to stay within V-QUEST's limit on sequences in one go
LOGGER = logging.getLogger(__name__)
LOGGER.propagate = False
LOGGER.addHandler(logging.StreamHandler())

def vquest_main(arglist=None):
    """Command-line interface for V-QUEST requests"""
    parser = __setup_arg_parser()
    if arglist is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arglist)
    LOGGER.setLevel(max(10, logging.WARNING - 10*args.verbose))
    LOGGER.debug("args parsed")
    # If nothing at all was given print the help and exit
    nonopts = ["config", "verbose"]
    args_set = {key: val for key, val in vars(args).items() if val}
    if not args_set:
        parser.print_help()
        sys.exit(1)
    LOGGER.debug("command-line arguments: %s",
        " ".join(["%s=%s" % (key, val) for key, val in args_set.items()]))
    # Overlay the default config, configs given as files, and then options
    # given as command line arguments
    configs = [load_config(config) for config in args.config]
    for filename, config in zip(args.config, configs):
        LOGGER.debug("options via %s: %s",
            filename,
            " ".join(["%s=%s" % (key, val) for key, val in config.items()]))
    vquest_args = {key: val for key, val in args_set.items() if key not in nonopts}
    LOGGER.debug("overriding command-line options: %s",
        " ".join(["%s=%s" % (key, val) for key, val in vquest_args.items()]))
    config_full = layer_configs(DEFAULTS, *configs, vquest_args)
    LOGGER.debug("final config: %s",
        " ".join(["%s=%s" % (key, val) for key, val in config_full.items()]))
    LOGGER.info("Configuration prepared")
    output = vquest(config_full)
    LOGGER.info("Writing vquest_airr.tsv")
    with open("vquest_airr.tsv", "wt") as f_out:
        f_out.write(output["vquest_airr.tsv"])
    LOGGER.info("Writing Parameters.txt")
    with open("Parameters.txt", "wt") as f_out:
        f_out.write(output["Parameters.txt"])
    LOGGER.info("Done.")

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
    supported = [("resultType", "excel"), ("xv_outputtype", 3)]
    if all([config.get(pair[0]) == pair[1] for pair in supported]):
        output = {}
        records = _parse_records(config)
        if not records:
            raise ValueError("No sequences supplied")
        LOGGER.info("Starting request batch for %d sequences total", len(records))
        for chunk in _chunker(records, CHUNK_SIZE):
            if output:
                time.sleep(DELAY)
            LOGGER.info("Sending request with %d sequences...", len(chunk))
            out_handle = StringIO()
            SeqIO.write(chunk, out_handle, "fasta")
            config_chunk = config.copy()
            config_chunk["sequences"] = out_handle.getvalue()
            config_chunk["inputType"] = "inline"
            response = requests.post(URL, data = config_chunk)
            response = _unzip(response.content)
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

def _chunker(iterator, chunksize):
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

def _unzip(txt):
    """Extract .zip data from bytes into dict keyed on filenames."""
    with BytesIO(txt) as f_in:
        zipobj = ZipFile(f_in)
        zipdata = {}
        for item in zipobj.infolist():
            with zipobj.open(item) as stream:
                zipdata[item.filename] = stream.read()
    return zipdata

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

def __setup_arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("config", nargs="*", help="YAML configuration file")
    parser.add_argument(
        "--verbose", "-v", action="count", default=0,
        help="increase logging verbosity")
    for opt_section in OPTIONS:
        option_parser = parser.add_argument_group(
            title="V-QUEST options: \"%s\" section" % opt_section["section"],
            description=opt_section["description"])
        for optname, opt in opt_section["options"].items():
            args = {
                "help": opt["description"]}
            if optname != "receptorOrLocusType":
                if isinstance(opt["values"], type):
                    args["type"] = opt["values"]
                else:
                    args["choices"] = opt["values"]
                    # Maybe helpful for long lists:
                    # https://stackoverflow.com/a/16985727/4499968
            option_parser.add_argument("--" + optname, **args)
    return parser

DEFAULTS = __load_default_config()
OPTIONS = __load_options()

if __name__ == "__main__":
    vquest_main()
