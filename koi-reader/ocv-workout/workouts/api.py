import logging

from .main import base_dir

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


LOGGER.info(base_dir)