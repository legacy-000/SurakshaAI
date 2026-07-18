"""TSE (Technical Support Engineer) diagnostic handlers.

Lives under ``common/support`` so deployment-system introspection routes share
a package — :mod:`tse_handler` is the implementation; this ``__init__`` is
the package marker so absolute imports like
``from common.support.tse_handler import ...`` resolve consistently inside
both the Advanced I/O function and any standalone test entry point.
"""
from common.support.tse_handler import TSEHandler

__all__ = ["TSEHandler"]
