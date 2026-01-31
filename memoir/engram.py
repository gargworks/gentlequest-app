"""
Engram Ledger - Cognitive Memory Model
=======================================
Part of the Nucleus Sovereign OS (N-SOS) core.
Defines 'Engrams': units of contextual memory that survive between agent sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class Engram:
    """A single unit of contextual memory."""
    def __init__(self, key: str, value: str, context: str, intensity: int = 5):
        self.key = key
        self.value = value
        self.context = context             # The 'Zoom Level' (Feature, Architecture, Brand)
        self.intensity = intensity         # 1-10 (How much should Claude care?)
        self.timestamp = datetime.utcnow().isoformat()
        self.signature = None              # Future: Cryptographic signing for sovereignty

    def to_dict(self) -> Dict:
        return self.__dict__

class EngramLedger:
    """The central storage for Engrams."""
    def __init__(self, brain_path: Path):
        self.path = brain_path / "engrams" / "ledger.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_engram(self, engram: Engram):
        """Append a new engram to the ledger."""
        with open(self.path, "a") as f:
            f.write(json.dumps(engram.to_dict()) + "\n")

    def query_context(self, context: str) -> List[Engram]:
        """Retrieve engrams for a specific strategic context."""
        results = []
        if not self.path.exists():
            return results
        
        with open(self.path, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Match by context or keyword in key/value
                    if (data.get("context", "").lower() == context.lower() or
                        context.lower() in data.get("key", "").lower() or
                        context.lower() in data.get("value", "").lower()):
                        engram = Engram(
                            key=data["key"],
                            value=data["value"],
                            context=data["context"],
                            intensity=data.get("intensity", 5)
                        )
                        engram.timestamp = data.get("timestamp")
                        engram.signature = data.get("signature")
                        results.append(engram)
        
        # Sort by intensity (highest first)
        results.sort(key=lambda e: e.intensity, reverse=True)
        return results
    
    def query_all(self) -> List[Engram]:
        """Retrieve all engrams from the ledger."""
        results = []
        if not self.path.exists():
            return results
        
        with open(self.path, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    engram = Engram(
                        key=data["key"],
                        value=data["value"],
                        context=data["context"],
                        intensity=data.get("intensity", 5)
                    )
                    engram.timestamp = data.get("timestamp")
                    engram.signature = data.get("signature")
                    results.append(engram)
        return results