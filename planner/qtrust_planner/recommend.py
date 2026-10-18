"""Deterministic target-algorithm recommendations for migration assets.

This module is deliberately a policy table, not a model: every recommendation
cites a standard, is reproducible, and can be explained to an auditor. The
GNN/RL layers decide *order*; this module decides *what to migrate to*.

Usage note: ``usage`` (a.k.a. ``asset_type``/``crypto_usage``) disambiguates
RSA/ECDSA keys used for signatures from those used for key exchange. When it
is absent, the recommendation says so and lowers its confidence.
"""

from __future__ import annotations

from typing import Any

ALREADY_PQC = ("ML-KEM", "ML-DSA", "SLH-DSA", "FALCON", "HQC", "SPHINCS", "KYBER", "DILITHIUM")

_SIGNATURE_HINTS = (
    "sig", "sign", "cert", "auth", "verify", "token", "jwt", "code-sign",
    "code_sign", "signature",
)
_KEM_HINTS = (
    "kem", "kex", "key_exchange", "key-exchange", "encrypt", "tls",
    "handshake", "dh", "key transport", "key_transport", "secret",
)


def _usage(asset: dict[str, Any]) -> str:
    raw = (
        asset.get("usage")
        or asset.get("asset_type")
        or asset.get("crypto_usage")
        or ""
    )
    return str(raw).strip().lower()


def _base(
    *,
    target: str,
    alternative: str,
    standard: str,
    category: str,
    rationale: str,
    confidence: float = 1.0,
    cnsa_alternative: str | None = None,
) -> dict[str, Any]:
    return {
        "target_algorithm": target,
        "alternative": alternative,
        "standard": standard,
        "category": category,
        "rationale": rationale,
        "confidence": confidence,
        "cnsa_2020_alternative": cnsa_alternative,
    }


def recommend_target(asset: dict[str, Any]) -> dict[str, Any]:
    """Return the recommended PQC target for one CBOM asset.

    Unknown algorithms never get a fabricated answer: they are routed to manual
    review with confidence 0.0.
    """
    algorithm = str(asset.get("algorithm") or "unknown").strip().upper()
    usage = _usage(asset)
    key_size = int(asset.get("key_size") or 0)

    if algorithm.startswith(ALREADY_PQC):
        return _base(
            target=algorithm,
            alternative="none",
            standard="FIPS 203/204/205 (already post-quantum)",
            category="already_pqc",
            rationale="Asset already uses a NIST PQC algorithm; verify parameter set and library support.",
        )

    signature_intent = any(hint in usage for hint in _SIGNATURE_HINTS)
    kem_intent = any(hint in usage for hint in _KEM_HINTS)

    if algorithm.startswith(("RSA", "ECDSA", "EDDSA", "DSA")) or "ECDSA" in algorithm:
        if kem_intent and not signature_intent:
            return _base(
                target="ML-KEM-768",
                alternative="X25519MLKEM768 (hybrid)",
                standard="FIPS 203",
                category="kem",
                rationale=(
                    "Declared usage is key establishment; ML-KEM-768 is the NIST "
                    "category-3 default, with a hybrid X25519+ML-KEM transition."
                ),
                cnsa_alternative="ML-KEM-1024",
            )
        if signature_intent:
            return _base(
                target="ML-DSA-65",
                alternative="SLH-DSA-SHA2-128s",
                standard="FIPS 204 (FIPS 205 alternative)",
                category="signature",
                rationale=(
                    "Declared usage is signatures; ML-DSA-65 is the NIST "
                    "category-3 default. Use SLH-DSA where hash-based assurance "
                    "or conservative verification is required."
                ),
                cnsa_alternative="ML-DSA-87",
            )
        return _base(
            target="ML-DSA-65",
            alternative="ML-KEM-768",
            standard="FIPS 204 (signatures) / FIPS 203 (key exchange)",
            category="signature_or_kem",
            rationale=(
                "Usage is not declared. RSA/ECDSA assets are usually signature "
                "keys (certs, JWT, code signing) but can be key transport; "
                "confirm the usage before choosing. ML-DSA-65 is the signature "
                "default, ML-KEM-768 the key-exchange default."
            ),
            confidence=0.75,
            cnsa_alternative="ML-DSA-87 / ML-KEM-1024",
        )

    if algorithm.startswith(("DH", "ECDH")) or "ECDHE" in algorithm:
        return _base(
            target="ML-KEM-768",
            alternative="X25519MLKEM768 (hybrid)",
            standard="FIPS 203",
            category="kem",
            rationale=(
                "Diffie-Hellman key agreement is replaced by ML-KEM; deploy the "
                "hybrid X25519MLKEM768 during the transition for interoperability."
            ),
            cnsa_alternative="ML-KEM-1024",
        )

    if algorithm.startswith(("AES", "3DES", "DES", "RC4", "CHACHA")):
        weak = algorithm.startswith(("3DES", "DES", "RC4")) or key_size < 256
        return _base(
            target="AES-256",
            alternative="AES-256-GCM / ChaCha20-Poly1305" if not weak else "AES-256-GCM",
            standard="FIPS 197 (AES); NIST SP 800-38D (GCM)",
            category="symmetric",
            rationale=(
                "Symmetric ciphers are not broken by Shor's algorithm, but "
                "CNSA 2.0 and long-lived-data policy require AES-256. "
                + ("The current algorithm/key size is below that bar." if weak else "Key size already meets AES-256.")
            ),
            confidence=0.95,
        )

    if "SHA" in algorithm or algorithm.startswith(("MD5", "MD4", "SHA1")):
        weak = algorithm.startswith(("MD5", "MD4", "SHA1", "SHA-1"))
        return _base(
            target="SHA-384",
            alternative="SHA-256 (minimum) / SHA3-384",
            standard="FIPS 180-4; CNSA 2.0 requires SHA-384+",
            category="hash",
            rationale=(
                "Hashes need larger digests for collision resistance and CNSA 2.0; "
                "SHA-384 is the CNSA 2.0 default for long-lived signatures."
                + (" The current hash is deprecated." if weak else "")
            ),
            confidence=0.95,
        )

    return _base(
        target="manual-review",
        alternative="none",
        standard="NIST IR 8547",
        category="unknown",
        rationale=(
            "Algorithm is not in the deterministic policy table. Capture the "
            "library, mode and usage before recommending a target; do not "
            "auto-migrate an unknown primitive."
        ),
        confidence=0.0,
    )
