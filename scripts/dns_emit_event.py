#!/usr/bin/env python3
"""
DNS Event Emission Helper
Emits DNS configuration events to brain ledger for cross-thread visibility
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Add MCP server to path
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_SRC = PROJECT_ROOT / "mcp-server-nucleus" / "src"
sys.path.insert(0, str(SERVER_SRC))

try:
    from mcp_server_nucleus.runtime.event_stream import emit_event, EventTypes, EventSeverity
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP event stream not available, using fallback logging")

BRAIN_PATH = PROJECT_ROOT / ".brain"
LEDGER_PATH = BRAIN_PATH / "ledger"
DNS_COMPLETIONS = LEDGER_PATH / "dns_completions.jsonl"


def emit_dns_event(event_type: str, domain: str, **kwargs):
    """
    Emit DNS event to brain ledger
    
    Args:
        event_type: Type of DNS event (cname_added, cname_verified, certificate_provisioned, etc.)
        domain: Domain name (e.g., hud.gentlequest.app)
        **kwargs: Additional metadata (provider, target, task_id, etc.)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build event metadata
    metadata = {
        "domain": domain,
        "event_type": event_type,
        "timestamp": timestamp,
        **kwargs
    }
    
    # Emit to MCP event stream if available
    if MCP_AVAILABLE:
        try:
            event_map = {
                "cname_added": EventTypes.INFRASTRUCTURE_CHANGE,
                "cname_verified": EventTypes.INFRASTRUCTURE_CHANGE,
                "certificate_provisioned": EventTypes.INFRASTRUCTURE_CHANGE,
                "dns_complete": EventTypes.TASK_COMPLETED,
            }
            
            severity_map = {
                "cname_added": EventSeverity.INFO,
                "cname_verified": EventSeverity.INFO,
                "certificate_provisioned": EventSeverity.INFO,
                "dns_complete": EventSeverity.INFO,
            }
            
            emit_event(
                event_type=event_map.get(event_type, EventTypes.INFRASTRUCTURE_CHANGE),
                severity=severity_map.get(event_type, EventSeverity.INFO),
                message=f"DNS {event_type.replace('_', ' ')} for {domain}",
                metadata=metadata
            )
            print(f"✅ Event emitted to MCP event stream: {event_type}")
        except Exception as e:
            print(f"⚠️  Failed to emit to MCP event stream: {e}")
    
    # Always write to DNS completions log
    try:
        LEDGER_PATH.mkdir(parents=True, exist_ok=True)
        
        with open(DNS_COMPLETIONS, 'a') as f:
            json.dump(metadata, f)
            f.write('\n')
        
        print(f"✅ Event logged to {DNS_COMPLETIONS}")
    except Exception as e:
        print(f"❌ Failed to log event: {e}")
        return False
    
    return True


def main():
    """CLI interface for emitting DNS events"""
    if len(sys.argv) < 3:
        print("Usage: dns_emit_event.py <event_type> <domain> [key=value ...]")
        print("")
        print("Event types:")
        print("  cname_added          - CNAME record added to DNS provider")
        print("  cname_verified       - CNAME verified via dig")
        print("  certificate_provisioned - SSL certificate provisioned")
        print("  dns_complete         - DNS configuration complete")
        print("")
        print("Examples:")
        print("  dns_emit_event.py cname_added hud.gentlequest.app provider=name.com target=ghs.googlehosted.com task_id=task-52661bba")
        print("  dns_emit_event.py cname_verified hud.gentlequest.app")
        print("  dns_emit_event.py certificate_provisioned hud.gentlequest.app")
        print("  dns_emit_event.py dns_complete hud.gentlequest.app")
        sys.exit(1)
    
    event_type = sys.argv[1]
    domain = sys.argv[2]
    
    # Parse additional key=value arguments
    kwargs = {}
    for arg in sys.argv[3:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            kwargs[key] = value
    
    print(f"Emitting DNS event: {event_type} for {domain}")
    if kwargs:
        print(f"Metadata: {kwargs}")
    
    success = emit_dns_event(event_type, domain, **kwargs)
    
    if success:
        print("✅ DNS event emitted successfully")
        sys.exit(0)
    else:
        print("❌ Failed to emit DNS event")
        sys.exit(1)


if __name__ == "__main__":
    main()
