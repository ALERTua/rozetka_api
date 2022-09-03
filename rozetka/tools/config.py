import os

import yaml
from pathlib import Path

CONFIG_DIR_PATH = os.getenv('CONFIG_DIR_PATH')
CONFIG_FILENAME = os.getenv('CONFIG_FILENAME')


def load_config():
    config = Path(CONFIG_DIR_PATH) / CONFIG_FILENAME
    with config.open() as fo:
        loaded = yaml.safe_load(fo)
    pass


if __name__ == '__main__':
    load_config()
    pass
