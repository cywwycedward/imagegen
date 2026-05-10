"""imagegen — CLI tool for generating images using NanoBanana API providers."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("imagegen")
except PackageNotFoundError:
    __version__ = "0.1.0"
