
import os
import sys
import shutil
import logging
from pathlib import Path

# Add src to path so we can import modules
sys.path.append(str(Path("mcp-server-nucleus/src").absolute()))

from mcp_server_nucleus.runtime.publisher import Publisher
from mcp_server_nucleus.runtime.installer import Installer
from mcp_server_nucleus.runtime.factory import ContextFactory
from mcp_server_nucleus.cli import handle_install_command

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

class MockArgs:
    def __init__(self, path):
        self.path = str(path)

def verify_flow():
    base_path = Path(".").absolute()
    brain_path = base_path / ".brain"
    packages_path = base_path / "packages"
    dist_path = base_path / "dist"
    
    # Clean dist
    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir()

    logger.info("1. Setup Environment")
    # Ensure brain exists
    if not brain_path.exists():
        logger.error("Brain not found. Run 'nucleus init' first.")
        return False

    logger.info("2. Publish Agent")
    publisher = Publisher(brain_path)
    key_manager = publisher.key_manager
    
    # For this verification, we might need to generate one if none exists.
    # But let's assume 'default' or similar if we can find it.
    
    # Check for keys in .brain/identity/keys or similar?
    # Actually, Publisher uses KeyManager. 
    # Let's peek at KeyManager to see how to get a valid key ID.
    # Check for keys in .brain/identity/keys or similar?
    # KeyManager stores keys in ledger/keystore.json via _load_keystore
    keystore = key_manager._load_keystore()
    keys = list(keystore.keys())
    
    if not keys:
        logger.info("No keys found. Generating a temporary key for verification.")
        key_id = key_manager.generate_key("verify-key")
    else:
        key_id = keys[0] # Use first available key
        
    logger.info(f"Using Key ID: {key_id}")
    
    # CRITICAL FIX for Verification:
    # TeamManager reads trusted_keys from config/team.json.
    # Installer passes these keys to NukeLoader.
    # NukeLoader expects PEMs.
    # We must ensure team.json has the PUBLIC KEY PEM, not just the ID.
    
    # Get the full key pair to access public pem
    kp = key_manager.get_key_pair(key_id)
    if not kp:
        logger.error(f"Could not retrieve key pair for {key_id}")
        return False
        
    team_config_path = brain_path / "config" / "team.json"
    team_config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Creates/Overwrites team config with this key as trusted
    import json
    team_config = {
        "team_id": "verify-team",
        "name": "Verification Team",
        "trusted_keys": [kp.public_key_pem], 
        "policy": {"require_signed": True}
    }
    team_config_path.write_text(json.dumps(team_config, indent=2))
    logger.info(f"Updated team.json with trusted key (PEM length: {len(kp.public_key_pem)})")
    
    researcher_src = packages_path / "researcher"
    artifact_path = publisher.publish(researcher_src, dist_path, key_id)
    
    if not artifact_path.exists():
        logger.error("Failed to generate artifact.")
        return False
        
    logger.info(f"Artifact created: {artifact_path}")
    
    logger.info("3. Install Agent (via CLI logic)")
    # Set env var for CLI to pick up correct brain path
    os.environ["NUCLEUS_BRAIN_PATH"] = str(brain_path)
    
    args = MockArgs(artifact_path)
    handle_install_command(args)
    
    logger.info("4. Verify Installation")
    # Check if files exist in installed location
    # NukeLoader installs into .brain/agents (or tools/installed depending on logic)
    # Our manifest says "nucleus.core.researcher"
    
    # Based on NukeLoader default logic (which we assume):
    # It might install metadata to ledger or agent file to agents/
    
    # Check agents dir
    agent_file = brain_path / "agents" / "researcher.md" # Name in manifest/agent_file
    if agent_file.exists():
        logger.info("✅ Agent file found in .brain/agents/")
    else:
        logger.warning(f"Agent file NOT found at {agent_file}. Checking other locations...")
        
    # 5. Runtime Verification
    logger.info("5. Runtime Load Verification")
    factory = ContextFactory(brain_path)
    
    # Try to load the persona
    try:
        context = factory.create_context_for_persona("test-session", "researcher", "Initial Test")
        if context.get("persona") == "Researcher":
             logger.info("✅ ContextFactory successfully loaded Researcher persona")
        else:
             logger.error(f"❌ ContextFactory loaded {context.get('persona')} instead of Researcher")
             return False
    except Exception as e:
        logger.error(f"❌ Failed to load context: {e}")
        return False

    logger.info("🎉 VERIFICATION SUCCESSFUL")
    return True

if __name__ == "__main__":
    success = verify_flow()
    sys.exit(0 if success else 1)
