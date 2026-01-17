#!/usr/bin/env python3
"""
verify_keymaster.py

Verification script for Phase 57: Chat 15 - The Keymaster.
Tests the Ed25519 Key Generation and TrustProfile implementation.
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.identity.keygen import KeyManager
from mcp_server_nucleus.runtime.identity.trust import TrustProfile, TrustLevel

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_KEYMASTER")

def verify_keygen():
    """
    Test Step 1: Generate Keypair
    """
    logger.info("Step 1: Testing KeyManager Key Generation...")
    
    # Generate new keypair
    key_manager = KeyManager()
    keys = key_manager.generate_keypair()
    
    if not keys.private_key_pem:
        logger.error("❌ Failed to generate private key PEM")
        return False
        
    if not keys.public_key_pem:
        logger.error("❌ Failed to generate public key PEM")
        return False
        
    if not keys.key_id:
        logger.error("❌ Failed to generate Key ID")
        return False
        
    logger.info(f"✅ Generated Key ID: {keys.key_id}")
    return keys

def verify_signing(keys):
    """
    Test Step 2: Sign and Verify Data
    """
    logger.info("Step 2: Testing Signing & Verification...")
    
    data = b"Hello Nucleus Marketplace"
    key_manager = KeyManager()
    
    # Sign
    signature = key_manager.sign(keys.private_key_pem, data)
    logger.info(f"✅ Generated Signature: {signature[:16]}...")
    
    # Verify (Good)
    is_valid = key_manager.verify(keys.public_key_pem, signature, data)
    if not is_valid:
        logger.error("❌ Signature verification failed for valid data")
        return False
        
    # Verify (Bad)
    is_invalid = key_manager.verify(keys.public_key_pem, signature, b"Tampered Data")
    if is_invalid:
        logger.error("❌ Signature verification SUCCEEDED for tampered data (Expected Failure)")
        return False
        
    logger.info("✅ Signature verification passed (Positive & Negative)")
    return True

def verify_trust_profile(keys):
    """
    Test Step 3: Create and Load TrustProfile
    """
    logger.info("Step 3: Testing TrustProfile...")
    
    profile = TrustProfile(
        publisher_id=keys.key_id,
        trust_level=TrustLevel.VERIFIED,
        label="Antigravity Test",
        public_key=keys.public_key_pem
    )
    
    json_str = profile.to_json()
    logger.info(f"✅ Serialized Profile: {json_str}")
    
    loaded = TrustProfile.from_json(json_str)
    
    if loaded.publisher_id != keys.key_id:
        logger.error(f"❌ Publisher ID mismatch: {loaded.publisher_id}")
        return False
        
    if loaded.trust_level != TrustLevel.VERIFIED:
        logger.error(f"❌ Trust Level mismatch: {loaded.trust_level}")
        return False
        
    logger.info("✅ TrustProfile serialization/deserialization passed")
    return True

def main():
    try:
        keys = verify_keygen()
        if not keys:
            sys.exit(1)
            
        if not verify_signing(keys):
            sys.exit(1)
            
        if not verify_trust_profile(keys):
            sys.exit(1)
            
        logger.info("✨ ALL KEYMASTER CHECKS PASSED ✨")
        sys.exit(0)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}. Make sure 'cryptography' is installed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
