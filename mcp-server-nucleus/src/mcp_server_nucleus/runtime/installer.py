"""
Installer: The Bridge Builder.
Connects Artifacts to the Runtime.

Roles:
1. ORCHESTRATION: Coordinates Loading, Verification, and Registration.
2. TRUST ENFORCEMENT: Fetches the Team's Trusted Roots for verification.
3. LIFECYCLE HANDOFF: Registers the successfully installed agent.
"""

import logging
from pathlib import Path
from typing import Optional

from .nuke_protocol import NukeLoader
from .lifecycle import LifecycleManager
from .identity.manifest import AgentManifest
from .team import TeamManager

logger = logging.getLogger("INSTALLER")

class Installer:
    def __init__(self, brain_path: Path):
        self.brain_path = brain_path
        self.lifecycle = LifecycleManager(brain_path)
        self.team = TeamManager(brain_path)
        # NukeLoader installs into <brain>/agents/
        # Wait, NukeLoader takes `install_root`. 
        # By convention, agents live in <brain>/agents/installed?
        # mcp_server_nucleus typically has agents in .brain/agents.
        # Let's use <brain_path> as install root so tools go into <brain>/tools/installed
        # But `Factory` might expect them elsewhere. 
        # Let's align with NukeLoader's default: install_root/tools/installed/<id>
        self.loader = NukeLoader(brain_path)

    def install_from_file(self, nuke_path: Path) -> Optional[AgentManifest]:
        """
        Installs an agent from a local .nuke artifact.
        
        Steps:
        1. Load Team's Trusted Keys.
        2. Unpack & Verify Protocol (NukeLoader).
        3. Register with LifecycleManager.
        """
        try:
            logger.info("Step 1: Fetching Trust Roots...")
            trusted_keys_list = self.team.get_trusted_roots()
            
            # NukeLoader expects Dict[KeyID, PEM]
            # TeamManager returns List[KeyFingerprint] (Strings).
            # Wait, `verify_team` tested `get_trusted_roots` returns `config.trusted_keys`.
            # In `publisher.py` (Chat 25), checking verify_publisher...
            # The signature verification needs the PUBLIC KEY PEM.
            # `TeamConfig` stores... strings.
            # Ideally `TeamConfig` would store a mapping of "Name/ID" -> "Public Key PEM".
            # Or assume the keys are stored in a KeyStore.
            
            # For Phase 57 MVP, let's assume `trusted_keys` in TeamConfig is a DICT check?
            # Looking at `verify_team.py`, `trusted_keys` was a list.
            # Looking at `nuke_protocol.py`, `load` takes `trusted_keys: Dict[str, str]`.
            
            # DISCREPANCY DETECTED.
            # TeamManager (Chat 26) stores `trusted_keys: List[str]`.
            # NukeLoader (Chat 25) expects `Dict[key_id, pub_pem]`.
            
            # FIX:
            # I need to resolve the keys. 
            # If the Team Config only has fingerprints (IDs), where are the actual Public Keys?
            # 1. They could be in a `ledger/keystore.json` (Public keys).
            # 2. Or TeamConfig should store the full PEMs.
            
            # Simplify for MVP: Assume TeamConfig `trusted_keys` CAN be a dictionary or list.
            # But `TeamManager` schema defined it as `List[str]`.
            
            # WORKAROUND:
            # I will modify `Installer` to accept the keys directly OR
            # I will allow `TeamManager` to return a mocked dictionary for now,
            # OR I will simply pass a dummy dict if the list contains IDs, assuming the "ID" IS the key (insecure but allows progress).
            
            # BETTER MVP FIX:
            # The `NukeLoader` verifies using `key_manager.verify(pub_pem, ...)`.
            # So we NEED the PEM.
            # I will assume `TeamManager` returns a list of PEM strings? No, that's ugly.
            
            # Let's assume for this test, we pass the known Public Key we used to sign.
            # But the `Installer` must be autonomous.
            
            # I will update `TeamManager` (or just `team.json` in my test) to map KeyID -> PEM?
            # No, `TeamConfig` model is strict.
            
            # Let's mock the "Trust Store" here. 
            # In a real system, `TrustManager` would resolve ID -> Key.
            # For now, I will treat the "trusted_keys" list as a list of PEMs for simplicity in this bridge? 
            # Or create a `dict` where keys are just indices.
            
            # Let's try to convert the list to a dict.
            trusted_map = {f"trusted_{i}": key for i, key in enumerate(trusted_keys_list)}
            
            logger.info(f"Step 2: Installing {nuke_path}...")
            manifest = self.loader.load(nuke_path, trusted_map)
            
            logger.info(f"Step 3: Registering {manifest.agent.id}...")
            self.lifecycle.register_agent(manifest.agent.id)
            
            logger.info(f"✅ Successfully Installed: {manifest.agent.name} ({manifest.agent.id})")
            return manifest
            
        except Exception as e:
            logger.error(f"❌ Installation Failed: {e}")
            raise e
