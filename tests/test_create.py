# coding: utf8

import otah


def test_creation():
    with open("openterm.plist") as f:
        original_data = f.read().replace("    ", "\t")

    with otah.Manifest("OpenTerm_NoPayload.ipa") as manifest:
        assert (
            manifest.create(
                "https://github.com/ongyx/ongyx.github.io/releases/download/1.0.0/OpenTerm.ipa"
            ).decode("utf8")
            == original_data
        )
