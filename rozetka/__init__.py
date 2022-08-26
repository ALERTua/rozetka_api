from global_logger import Log
from pathlib import Path

name = 'rozetka'
logs_dir = Path.cwd() / f'{name}_logs'
logs_dir.mkdir(parents=True, exist_ok=True)  # todo:
LOG = Log.get_logger(name, logs_dir=logs_dir)
