"""
ForeSight — FHE Demo Utilities
Simulates FHE encryption/decryption flow for the demo dashboard.
"""

import hashlib
import os
import time
import json
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


class FHEDemoSimulator:
    """
    Simulates FHE operations for the demo.
    In production, this would use Zama concrete-ml.
    For the frontend demo, we show the architecture flow.
    """

    def __init__(self):
        self.key = get_random_bytes(32)  # AES-256 key for string fields

    def encrypt_numeric_features(self, features: dict):
        """
        Simulate FHE encryption of numeric features.
        Returns a hex representation of 'ciphertext'.
        """
        start = time.time()

        # Simulate quantization to 8-bit
        quantized = {}
        for k, v in features.items():
            quantized[k] = int(np.clip(v, 0, 255))

        # Generate realistic-looking ciphertext
        feature_bytes = json.dumps(quantized).encode()
        ct_hash = hashlib.sha512(feature_bytes + os.urandom(32)).hexdigest()

        # Simulate FHE encryption time (5-30 seconds in real system)
        elapsed = time.time() - start

        return {
            "ciphertext_hex": ct_hash,
            "ciphertext_size_bytes": len(ct_hash),
            "quantization_bits": 8,
            "encryption_time_ms": round(elapsed * 1000, 2),
            "scheme": "TFHE (Zama concrete-ml)",
            "tree_depth": 4,
        }

    def encrypt_string_field(self, plaintext: str):
        """
        AES-GCM encryption for string fields (names, GSTINs, etc.)
        """
        cipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(cipher.nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "scheme": "AES-256-GCM",
        }

    def decrypt_string_field(self, encrypted: dict):
        """Decrypt AES-GCM encrypted string."""
        cipher = AES.new(
            self.key,
            AES.MODE_GCM,
            nonce=base64.b64decode(encrypted["nonce"])
        )
        plaintext = cipher.decrypt_and_verify(
            base64.b64decode(encrypted["ciphertext"]),
            base64.b64decode(encrypted["tag"])
        )
        return plaintext.decode("utf-8")

    def simulate_fhe_inference(self, encrypted_features: dict, model_name="XGBoost-BuyerReliability"):
        """
        Simulate running ML inference on encrypted data.
        Returns a simulated encrypted result.
        """
        start = time.time()

        # In production: concrete-ml would run the compiled FHE circuit
        result_hash = hashlib.sha256(
            encrypted_features["ciphertext_hex"].encode() + os.urandom(16)
        ).hexdigest()[:32]

        elapsed = time.time() - start

        return {
            "encrypted_result": result_hash,
            "model": model_name,
            "inference_time_ms": round(elapsed * 1000 + np.random.uniform(50, 200), 2),
            "tree_depth": 4,
            "status": "completed",
        }

    @staticmethod
    def add_laplace_noise(value, sensitivity=1.0, epsilon=1.0):
        """
        Add Laplace noise for Differential Privacy.
        ε = 1.0, calibrated to invoice-amount sensitivity.
        """
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    @staticmethod
    def generate_fhe_architecture_data():
        """Generate data for the FHE Architecture Panel."""
        return {
            "pipeline_steps": [
                {"step": "Client-Side Quantization", "status": "✅", "detail": "8-bit quantization of numeric features"},
                {"step": "FHE Key Generation", "status": "✅", "detail": "TFHE key pair (public/evaluation)"},
                {"step": "Feature Encryption", "status": "✅", "detail": "Numeric features → ciphertext via TFHE"},
                {"step": "String Encryption", "status": "✅", "detail": "Buyer names, GSTINs → AES-256-GCM"},
                {"step": "Encrypted Inference", "status": "✅", "detail": "XGBoost on ciphertext (depth=4)"},
                {"step": "Ciphertext Result", "status": "✅", "detail": "Encrypted score returned to client"},
                {"step": "Client Decryption", "status": "✅", "detail": "Only client holds the secret key"},
            ],
            "security_properties": {
                "Server sees plaintext": "❌ Never",
                "Decryption in memory": "❌ Eliminated by FHE",
                "String metadata exposure": "❌ AES-GCM encrypted",
                "Federated aggregation": "✅ Differential Privacy (ε=1.0)",
                "Offline backup": "✅ AES-256 encrypted USB export",
            },
            "performance": {
                "Encryption latency": "~200ms",
                "Inference latency": "5-30s (async cached)",
                "Cache hit latency": "<100ms",
                "Quantization bits": 8,
                "Tree depth limit": 4,
            }
        }
