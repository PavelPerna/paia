# content of conftest.py
import pytest

@pytest.fixture(scope="module", autouse=True)
def setup():
    import os
    import sys
    parent_path = os.path.abspath(os.path.join(str(__file__),'..','..','..'))
    sys.path.append(parent_path)