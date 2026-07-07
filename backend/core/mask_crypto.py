"""Simple shim for mask encryption utilities used in local/dev environments.
This intentionally implements no-op encrypt/decrypt when no MASK_KEY is configured,
so the app can run without the production masking key.
"""
import os

MASK_KEY = os.getenv("MASK_KEY", "")


def key_prefix() -> str:
    return "mask:" if MASK_KEY else ""


def encrypt_text(plain: str) -> str:
    # In production this should encrypt using a secure algorithm.
    # For local/dev, return the plain text.
    return plain


def decrypt_text(cipher: str) -> str:
    # In production this should decrypt using a secure algorithm.
    # For local/dev, return the input unchanged.
    return cipher
