import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))
os.environ.setdefault('DISABLE_BACKGROUND_TASKS', '1')

from pytest import main

if __name__ == '__main__':
    exit(main(['-q', 'tests/test_multi_currency.py']))
