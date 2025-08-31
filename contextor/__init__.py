"""Contextor - Convert documentation trees to Model Context Protocol files.

Contextor converts existing documentation trees (e.g. Next.js, Tailwind CSS)
into Model Context Protocol (.mdc) files optimized for LLMs.
"""

__version__ = "0.0.1"
__author__ = "Contextor Team"
__license__ = "MIT"

from .utils import content_hash, slugify

__all__ = ["slugify", "content_hash"]
