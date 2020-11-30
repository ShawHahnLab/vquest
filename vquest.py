#!/usr/bin/env python

"""
IMGT V-QUEST requests via imgt.org.

http://www.imgt.org/IMGT_vquest/analysis
"""

import sys
import subprocess
import argparse
import logging
from pathlib import Path
import yaml
import requests

URL = "http://www.imgt.org/IMGT_vquest/analysis"
LOGGER = logging.getLogger(__name__)
LOGGER.propagate = False
LOGGER.addHandler(logging.StreamHandler())

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

def __setup_arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        #formatter_class=argparse.RawDescriptionHelpFormatter)
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

def vquest_main():
    """Command-line interface for V-QUEST requests"""
    parser = __setup_arg_parser()
    args = parser.parse_args()
    LOGGER.setLevel(max(10, logging.WARNING - 10*args.verbose))
    LOGGER.debug("args parsed")
    args_set = {key: val for key, val in vars(args).items() if val}
    if not args_set:
        parser.print_help()
        sys.exit(1)
    LOGGER.debug(" ".join(["%s=%s" % (key, val) for key, val in args_set.items()]))
    configs = [load_config(config) for config in args.config]
    config_full = layer_configs(DEFAULTS, *configs)
    vquest(config_full)

def vquest(config):
    """Submit a request to V-QUEST"""
    print(config)
    #vquest_post(config)

def vquest_post(post_data):
    """Submit a single POST request to V-QUEST"""
    result = requests.post(URL, data = post_data)
    print(result)

def vquest_curl(post_data):
    """Submit a single POST request to V-QUEST via curl"""
    args = [('-F', '"%s=%s"' % (key, val)) for key, val in post_data.items()]
    args = [item for sublist in args for item in sublist]
    args = ["curl"] + args + ["--output", "test.zip", URL]

    result = subprocess.run(args, capture_output=True, check=True)
    print(result)
    print(result.stdout)
    print(result.stderr)

def __load_options():
    data = load_config(Path(__file__).parent / "data" / "options.yml")
    mapping = {"int": int, "bool": bool}
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

if __name__ == "__main__":
    vquest_main()
