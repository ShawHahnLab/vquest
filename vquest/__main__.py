"""
Command-line interface for vquest
"""

import sys
import logging
import argparse
import vquest
from vquest import LOGGER
from . import request
from .config import DEFAULTS, OPTIONS, load_config, layer_configs
from .util import airr_to_fasta
from .version import __version__

def main(arglist=None):
    """Command-line interface for V-QUEST requests"""
    # Parse command-line arguments either from a list or sys.argv.
    parser = __setup_arg_parser()
    if arglist is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arglist)
    LOGGER.setLevel(max(10, logging.WARNING - 10*args.verbose))
    args_set = {k: v for k, v in vars(args).items() if v is not None}
    # All the possible vquest options.  They're grouped by section as the keys
    # to inner dictionaries.
    vquest_opts = []
    for opt_section in OPTIONS:
        vquest_opts.extend(opt_section["options"].keys())
    vquest_args = {k: v for k, v in args_set.items() if k in vquest_opts}
    # If no config file(s) and no vquest args were given, just print the help
    # and exit
    if not vquest_args and not args.config:
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
    LOGGER.debug("overriding command-line options: %s",
        " ".join(["%s=%s" % (key, val) for key, val in vquest_args.items()]))
    config_full = layer_configs(DEFAULTS, *configs, vquest_args)
    LOGGER.debug("final config: %s",
        " ".join(["%s=%s" % (key, val) for key, val in config_full.items()]))
    LOGGER.info("Configuration prepared")
    output = request.vquest(config_full)
    if args.align:
        LOGGER.info("Writing FASTA to stdout")
        print(airr_to_fasta(output["vquest_airr.tsv"]), end="")
    else:
        LOGGER.info("Writing vquest_airr.tsv")
        with open("vquest_airr.tsv", "wt") as f_out:
            f_out.write(output["vquest_airr.tsv"])
        LOGGER.info("Writing Parameters.txt")
        with open("Parameters.txt", "wt") as f_out:
            f_out.write(output["Parameters.txt"])
    LOGGER.info("Done.")

def __setup_arg_parser():
    parser = argparse.ArgumentParser(
        description=vquest.__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("config", nargs="*", help="YAML configuration file")
    parser.add_argument(
        "--verbose", "-v", action="count", default=0,
        help="increase logging verbosity")
    parser.add_argument(
        "--version", "-V", action="version", version=__version__)
    parser.add_argument(
        "--align", "-a", action="store_true",
        help=("Instead of writing results to files, "
            "extract the sequence_id and sequence_alignment columns "
            "from AIRR results and print as FASTA.  "
            "If there is no text in the sequence_alignment column "
            "for a given sequence the original sequence is used instead."))
    for opt_section in OPTIONS:
        option_parser = parser.add_argument_group(
            title="V-QUEST options: \"%s\" section" % opt_section["section"],
            description=opt_section["description"])
        for optname, opt in opt_section["options"].items():
            args = {
                "help": opt["description"]}
            # receptorOrLocusType is a special case, but otherwise the pattern is:
            # "values" can be an actual type, like bool, or is assumed to be a
            # list of possible values.  In the latter case the type is taken to
            # be the inferred type of the first entry in the list.
            if optname != "receptorOrLocusType":
                if isinstance(opt["values"], type):
                    args["type"] = opt["values"]
                else:
                    args["choices"] = opt["values"]
                    args["type"] = type(opt["values"][0])
                    # Maybe helpful for long lists:
                    # https://stackoverflow.com/a/16985727/4499968
            option_parser.add_argument("--" + optname, **args)
    return parser

if __name__ == "__main__":
    main()
