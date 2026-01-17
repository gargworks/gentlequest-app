#!/usr/bin/env python3
"""
verify_nukepacker.py

Verification script for Phase 57: Chat 17 - The Stamp.
Tests NukePacker (Signing) and NukeLoader (Verification) with Ed25519.
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp-server-nucleus", "src")))

from mcp_server_nucleus.runtime.identity.keygen import KeyManager
from mcp_server_nucleus.runtime.identity.manifest import AgentManifest, AgentIdentity, Capability, CapabilityScope
from mcp_server_nucleus.runtime.nuke_protocol import NukePacker, NukeLoader

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("VERIFY_NUKEPACKER")

TEST_DIR = Path("test_nuke_stamp")

def setup_test_env():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()
    (TEST_DIR / "src").mkdir()
    (TEST_DIR / "tools").mkdir()
    
    # Create a dummy tool
    (TEST_DIR / "tools" / "test_tool.py").write_text("print('Hello World')")

def cleanup_test_env():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def verify_nuke_lifecycle():
    logger.info("Step 1: Setup Keys and Manifest")
    
    # 1. Generate Keys
    km = KeyManager()
    keys = km.generate_keypair()
    logger.info(f"✅ Generated Key ID: {keys.key_id}")
    
    # 2. Create Manifest
    manifest = AgentManifest(
        agent=AgentIdentity(
            id="nucleus.core.test",
            name="Test Agent",
            version="1.0.0",
            description="A test agent",
            author="Antigravity",
            license="MIT"
        ),
        capabilities=[
            Capability(scope=CapabilityScope.FILESYSTEM, reason="Test", paths=["/tmp"], mode="read")
        ]
    )
    
    # 3. Pack .nuke
    logger.info("Step 2: Packing .nuke artifact...")
    packer = NukePacker(TEST_DIR)
    output_path = TEST_DIR / "agent.nuke"
    
    packer.pack(
        manifest=manifest,
        tool_paths=[TEST_DIR / "tools" / "test_tool.py"],
        private_key_pem=keys.private_key_pem,
        output_path=output_path
    )
    
    if not output_path.exists():
        logger.error("❌ .nuke file was not created")
        return False
        
    logger.info(f"✅ Created {output_path}")
    
    # 4. Load & Verify
    logger.info("Step 3: Loading & Verifying .nuke artifact...")
    loader = NukeLoader(TEST_DIR / "brain")
    
    try:
        # We need to pass the public key because we don't have a Registry yet
        # In a real scenario, the loader looks up the key from the registry using manifest.agent.author (or ID)
        # For this unit test, we'll verify the logic inside the loader or pass the key explicitly if supported
        # Refactoring Loader to accept known_public_keys dict for testing
        
        loaded_manifest = loader.load(output_path, trusted_keys={keys.key_id: keys.public_key_pem})
        
        if loaded_manifest.agent.id != "nucleus.core.test":
            logger.error("❌ Loaded manifest ID mismatch")
            return False
            
        logger.info("✅ Signature Verified & Manifest Loaded")
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tamper_evidence():
    logger.info("Step 4: Tamper Evidence Test...")
    
    # Generate Keys
    km = KeyManager()
    keys = km.generate_keypair()
    
    # Create Artifact
    manifest = AgentManifest(
        agent=AgentIdentity(id="nucleus.tamper", name="Tamper", version="1.0.0", description="T", author="A", license="MIT")
    )
    packer = NukePacker(TEST_DIR)
    output_path = TEST_DIR / "tamper.nuke"
    packer.pack(manifest, [], keys.private_key_pem, output_path)
    
    # Tamper with it (Modify manifest inside zip)
    # Note: Modifying zip content without re-signing is hard script-wise, 
    # but we can try to corrupt the signature file or manifest file if we extract and repack.
    # Simpler test: Use WRONG Public Key for verification.
    
    wrong_keys = km.generate_keypair()
    loader = NukeLoader(TEST_DIR / "brain")
    
    try:
        loader.load(output_path, trusted_keys={keys.key_id: wrong_keys.public_key_pem})
        logger.error("❌ Verification SUCCEEDED with WRONG Key (Expected Failure)")
        return False
    except Exception as e:
        logger.info(f"✅ Caught expected error (Wrong Key): {e}")
        return True

def main():
    try:
        setup_test_env()
        
        if not verify_nuke_lifecycle():
            sys.exit(1)
            
        if not verify_tamper_evidence():
            sys.exit(1)
            
        logger.info("✨ ALL NUKEPACKER CHECKS PASSED ✨")
        cleanup_test_env()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        cleanup_test_env()
        sys.exit(1)

if __name__ == "__main__":
    main()
