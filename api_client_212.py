"""Backward compatible import shim.

Deprecated: import from server.client212 instead.
"""

from server.client212 import Client212, RateLimit

__all__ = ["Client212", "RateLimit"]
