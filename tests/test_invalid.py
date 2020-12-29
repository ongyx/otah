# coding: utf8

import otah
import pytest


def test_invalid():
    with pytest.raises(RuntimeError):
        otah.Manifest("invalid.ipa")
