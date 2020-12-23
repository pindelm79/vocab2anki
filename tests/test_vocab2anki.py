import pytest
from vocab2anki import __version__
from vocab2anki.vocab2anki import Anki


def test_version():
    assert __version__ == "0.1.0"
