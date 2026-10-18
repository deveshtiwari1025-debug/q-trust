"""Deterministic target-recommendation policy tests."""

from qtrust_planner.recommend import recommend_target


def test_rsa_signature_gets_ml_dsa_65():
    rec = recommend_target({"algorithm": "RSA-2048", "usage": "signature"})
    assert rec["target_algorithm"] == "ML-DSA-65"
    assert rec["category"] == "signature"
    assert "FIPS 204" in rec["standard"]
    assert rec["cnsa_2020_alternative"] == "ML-DSA-87"


def test_rsa_key_exchange_gets_ml_kem_768():
    rec = recommend_target({"algorithm": "RSA-2048", "usage": "key_exchange"})
    assert rec["target_algorithm"] == "ML-KEM-768"
    assert rec["category"] == "kem"
    assert "FIPS 203" in rec["standard"]


def test_rsa_without_usage_is_honest_about_ambiguity():
    rec = recommend_target({"algorithm": "RSA-2048"})
    assert rec["target_algorithm"] == "ML-DSA-65"
    assert rec["alternative"] == "ML-KEM-768"
    assert rec["category"] == "signature_or_kem"
    assert rec["confidence"] < 1.0


def test_ecdsa_tls_gets_hybrid_kem():
    rec = recommend_target({"algorithm": "ECDSA-P256", "usage": "tls handshake"})
    assert rec["target_algorithm"] == "ML-KEM-768"
    assert "X25519MLKEM768" in rec["alternative"]


def test_dh_gets_ml_kem_768():
    rec = recommend_target({"algorithm": "DH-2048", "usage": "key agreement"})
    assert rec["target_algorithm"] == "ML-KEM-768"


def test_aes_128_upgrades_to_256():
    rec = recommend_target({"algorithm": "AES-128", "key_size": 128, "usage": "encryption"})
    assert rec["target_algorithm"] == "AES-256"
    assert rec["category"] == "symmetric"


def test_sha1_upgrades_to_sha384():
    rec = recommend_target({"algorithm": "SHA-1", "usage": "hash"})
    assert rec["target_algorithm"] == "SHA-384"
    assert "deprecated" in rec["rationale"]


def test_already_pqc_is_preserved():
    rec = recommend_target({"algorithm": "ML-KEM-768", "key_size": 768})
    assert rec["category"] == "already_pqc"
    assert rec["target_algorithm"] == "ML-KEM-768"
    assert rec["alternative"] == "none"


def test_unknown_algorithm_is_manual_review():
    rec = recommend_target({"algorithm": "PROPRIETARY-CIPHER", "key_size": 99})
    assert rec["target_algorithm"] == "manual-review"
    assert rec["category"] == "unknown"
    assert rec["confidence"] == 0.0


def test_recommendation_is_deterministic():
    asset = {"algorithm": "RSA-2048", "usage": "code signing"}
    assert recommend_target(asset) == recommend_target(dict(asset))
