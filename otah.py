# coding: utf8
"""
create OTA manifests from iOS .ipa files for distribution outside the App Store.
"""

import pathlib
import plistlib
import re
import socket
import zipfile
from typing import IO, Optional, Union

__version__ = "0.1.1"

# find the app name, the .ipa file may be named differently.
RE_PLIST_PATH = re.compile(r"Payload/(\w+).app/?(.*)")


def _parse_app_name(zfile: zipfile.ZipFile) -> str:
    for path in zfile.namelist():
        match = RE_PLIST_PATH.match(path)
        if match is not None:
            return match.group(1)

    return ""  # should not happen, unless the .ipa file is invalid


# https://stackoverflow.com/a/28950776
def _get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


class Manifest:
    """An OTA manifest.

    Args:
        path: Path to the .ipa file to generate the manifest for.
    Attributes:
        zfile (zipfile.ZipFile): The .ipa file handle.
        appname (str): The app name (NOT the bundle id).
        info (dict): Loaded Info.plist.
    """

    def __init__(self, path: Union[str, pathlib.Path]):
        self._path = path if isinstance(path, pathlib.Path) else pathlib.Path(path)
        self.zfile = zipfile.ZipFile(self._path)
        self.appname = _parse_app_name(self.zfile)

        if self.appname:
            with self.zfile.open(f"Payload/{self.appname}.app/Info.plist") as f:
                self.info = plistlib.load(f)
        else:
            raise RuntimeError(
                f".ipa file at {self._path} is invalid: Could not detect app name"
            )

    def create(
        self,
        host: str,
        secure: bool = True,
        filehandle: Optional[IO] = None,
    ) -> bytes:
        """Create a manifest plist for this app.

        Args:
            host: The IP address/domain name plus the path to the app.
            (i.e 'http(s)://mywebsite.com/path/to/ipa').
            filehandle: The file to write the plist'd manifest to.
                The file must be opened as writable and in bytes mode (i.e, 'wb').
                If None, this is ignored. Defaults to None.

        Returns:
            The plist'd manifest, as bytes.
        """

        plist_data = plistlib.dumps(
            {
                "items": [
                    {
                        "assets": [
                            {
                                "kind": "software-package",
                                "url": host,
                            }
                        ],
                        "metadata": {
                            "bundle-identifier": self.info["CFBundleIdentifier"],
                            "bundle-version": self.info["CFBundleShortVersionString"],
                            "kind": "software",
                            "title": self.appname,
                        },
                    }
                ]
            },
            sort_keys=False,
        )

        if filehandle is not None:
            filehandle.write(plist_data)

        return plist_data

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        self.zfile.close()


def _main():
    import argparse
    import functools
    import sys
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer

    parser = argparse.ArgumentParser(prog="otah", description=__doc__)
    parser.add_argument("ipa_file", help=".ipa file to create manifest for")
    parser.add_argument(
        "-o", "--output", default=None, help="save plist'd manifest to file"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="where the .ipa file is hosted (i.e https://mywebsite.com/myapp.ipa)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="port to host server at (use with --demo)",
    )
    parser.add_argument(
        "-d",
        "--demo",
        action="store_true",
        help=(
            "test OTA by serving directory of the .ipa file and "
            "outputting the manifest there"
        ),
    )

    args = parser.parse_args()

    with Manifest(args.ipa_file) as manifest:
        if not args.demo and args.host:
            # production
            data = manifest.create(
                args.host,
                filehandle=open(args.output, "wb") if args.output is not None else None,
            )
            print(data)
        elif args.demo:
            # demo, use localhost
            localhost = _get_ip()
            host = f"https://{localhost}:{args.port}/{manifest._path.name}"
            manifest_path = manifest._path.parent / "manifest.plist"
            with manifest_path.open("wb") as f:
                manifest.create(host, f)

            # start local server
            handler = functools.partial(
                SimpleHTTPRequestHandler, directory=str(manifest._path.parent)
            )
            with TCPServer(("", args.port), handler) as httpd:
                address = f"{localhost}:{args.port}"
                print(f"serving at {address}")
                print(f"install {manifest.appname} on your iDevice using 'itms-services://?action=download-manifest&url={address}/manifest.plist'")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("exiting")
                    manifest_path.unlink()
                    sys.exit(0)
        else:
            print("Hostname not provided (did you mean --demo?)")


if __name__ == "__main__":
    _main()
