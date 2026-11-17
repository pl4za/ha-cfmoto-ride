"""CFMOTO RIDE cloud integration. Logic lives in hub.py so updates never need to touch this file."""
from .hub import CfmotoConfigEntry, async_setup_entry, async_unload_entry  # noqa: F401
