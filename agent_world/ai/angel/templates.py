"""Stub helpers for Angel prompt templates."""

from __future__ import annotations


def get_world_constraints_for_angel() -> dict:
    """Return world constraint information for Angel LLM."""
    return {}


def get_code_scaffolds_for_angel() -> dict:
    """Return code scaffold snippets for Angel LLM."""
    return {}


__all__ = [
    "get_world_constraints_for_angel",
    "get_code_scaffolds_for_angel",
]

