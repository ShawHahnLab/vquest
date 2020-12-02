"""
Command-line interface for vquest
"""

import sys
import logging
import argparse
import vquest
from . import LOGGER, DEFAULTS, OPTIONS
from . import load_config
from . import layer_configs

def main(arglist=None):
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
    output = vquest.vquest(config_full)
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

if __name__ == "__main__":
    main()
