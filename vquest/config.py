"""
Tools to manage configurations and default options.
"""

from pathlib import Path
import logging
import yaml

LOGGER = logging.getLogger(__name__)

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
