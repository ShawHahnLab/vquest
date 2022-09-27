"""
IMGT V-QUEST requests via imgt.org.

http://www.imgt.org/IMGT_vquest/analysis
"""

import logging
from .version import __version__
from .request import vquest
from .config import DEFAULTS, OPTIONS, load_config, layer_configs
LOGGER = logging.getLogger(__name__)
LOGGER.propagate = False
LOGGER.addHandler(logging.StreamHandler())
