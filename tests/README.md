# **NOTES**

This test folder contains a stripped-down version of the OpenTerm .ipa file (to keep this repo small).
To create the resources, run `build_res.py`.

## `test_create.py`

The original OpenTerm plist I created by hand uses 4 spaces for indentation, but the output of otah (by plistlib) uses tabs `\t`. So I had to replace the indent for this test to pass.
