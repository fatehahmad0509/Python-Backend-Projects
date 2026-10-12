#!/usr/bin/env python3
"""
MessageLMS — VAPID Key Generator
Run this ONCE, then paste the output into Railway environment variables.

Usage:
    pip install cryptography
    python generate_vapid.py
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64


def main():
    # Generate EC P-256 private key (required by Web Push / VAPID spec)
    key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # --- Private key: raw 32-byte scalar (d), base64url encoded ---
    raw_private = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    priv_b64 = base64.urlsafe_b64encode(raw_private).rstrip(b"=").decode()

    # --- Public key: 65-byte uncompressed EC point (0x04 || x || y) ---
    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()

    line = "=" * 65
    print(line)
    print("  VAPID Keys — Add to Railway Environment Variables")
    print(line)
    print()
    print(f"VAPID_PUBLIC_KEY={pub_b64}")
    print(f"VAPID_PRIVATE_KEY={priv_b64}")
    print(f"VAPID_MAILTO=mailto:admin@messagelms.com")
    print()
    print(line)
    print("VAPID_PUBLIC_KEY is served via GET /config and used by the browser.")
    print("Keep VAPID_PRIVATE_KEY secret — it only lives on the server.")
    print(line)


if __name__ == "__main__":
    main()
