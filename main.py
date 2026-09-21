import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config
from gui.app import main


if __name__ == "__main__":
    cfg = load_config()
    main(cfg)