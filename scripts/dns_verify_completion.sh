#!/bin/bash
# DNS Completion Verification Script
# Prevents rework by checking DNS status before starting configuration

set -e

BRAIN_PATH="/Users/lokeshgarg/ai-mvp-backend/.brain"
LEDGER_PATH="$BRAIN_PATH/ledger"
DNS_COMPLETIONS="$LEDGER_PATH/dns_completions.jsonl"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "DNS Completion Verification"
echo "======================================"
echo ""

# Function to check DNS CNAME
check_dns_cname() {
    local domain=$1
    local expected_target=$2
    
    echo -n "Checking DNS for $domain... "
    result=$(dig "$domain" CNAME +short 2>/dev/null | head -1)
    
    if [ -z "$result" ]; then
        echo -e "${RED}NOT CONFIGURED${NC}"
        return 1
    elif [ "$result" = "$expected_target" ]; then
        echo -e "${GREEN}CONFIGURED${NC} ($result)"
        return 0
    else
        echo -e "${YELLOW}CONFIGURED${NC} but unexpected target: $result"
        return 2
    fi
}

# Function to check nameservers
check_nameservers() {
    local domain=$1
    
    echo -n "Checking nameservers for $domain... "
    ns=$(dig "$domain" NS +short 2>/dev/null | head -1)
    
    if [ -z "$ns" ]; then
        echo -e "${RED}NONE FOUND${NC}"
        return 1
    else
        echo -e "${GREEN}$ns${NC}"
        
        # Identify provider
        if echo "$ns" | grep -q "cloudflare"; then
            echo "  → Provider: Cloudflare"
        elif echo "$ns" | grep -q "name.com"; then
            echo "  → Provider: name.com"
        else
            echo "  → Provider: Unknown"
        fi
        return 0
    fi
}

# Function to check Cloud Run domain mapping
check_cloud_run_mapping() {
    local domain=$1
    
    echo -n "Checking Cloud Run mapping for $domain... "
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${YELLOW}gcloud not installed${NC}"
        return 2
    fi
    
    result=$(gcloud beta run domain-mappings describe \
        --domain="$domain" \
        --project=gen-lang-client-0894185576 \
        --region=us-central1 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$result" = "NOT_FOUND" ]; then
        echo -e "${RED}NOT FOUND${NC}"
        return 1
    fi
    
    # Check certificate status
    cert_status=$(echo "$result" | grep -A 1 "CertificateProvisioned" | grep "status:" | awk '{print $2}' | tr -d "'")
    
    if [ "$cert_status" = "True" ]; then
        echo -e "${GREEN}READY${NC} (Certificate provisioned)"
        return 0
    else
        echo -e "${YELLOW}PENDING${NC} (Certificate: $cert_status)"
        return 2
    fi
}

# Function to check completion markers
check_completion_markers() {
    local domain=$1
    
    echo -n "Checking completion markers for $domain... "
    
    if [ ! -f "$DNS_COMPLETIONS" ]; then
        echo -e "${YELLOW}No completion log${NC}"
        return 2
    fi
    
    if grep -q "\"domain\": \"$domain\"" "$DNS_COMPLETIONS" 2>/dev/null; then
        last_entry=$(grep "\"domain\": \"$domain\"" "$DNS_COMPLETIONS" | tail -1)
        timestamp=$(echo "$last_entry" | grep -o '"timestamp": "[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}FOUND${NC} (Last: $timestamp)"
        return 0
    else
        echo -e "${YELLOW}NOT FOUND${NC}"
        return 1
    fi
}

# Function to check recent events
check_recent_events() {
    echo -n "Checking recent DNS events... "
    
    if [ ! -f "$LEDGER_PATH/events.jsonl" ]; then
        echo -e "${YELLOW}No events log${NC}"
        return 2
    fi
    
    dns_events=$(tail -50 "$LEDGER_PATH/events.jsonl" 2>/dev/null | grep -i "dns\|cname" | wc -l | tr -d ' ')
    
    if [ "$dns_events" -gt 0 ]; then
        echo -e "${GREEN}$dns_events events found${NC}"
        echo "  Recent DNS events:"
        tail -50 "$LEDGER_PATH/events.jsonl" 2>/dev/null | grep -i "dns\|cname" | tail -3 | while read line; do
            msg=$(echo "$line" | grep -o '"message": "[^"]*"' | cut -d'"' -f4)
            echo "    - $msg"
        done
        return 0
    else
        echo -e "${YELLOW}No recent DNS events${NC}"
        return 1
    fi
}

# Main verification
echo "=== hud.gentlequest.app ==="
echo ""
check_dns_cname "hud.gentlequest.app" "ghs.googlehosted.com."
dns_status_gentlequest=$?

check_nameservers "gentlequest.app"
check_cloud_run_mapping "hud.gentlequest.app"
cr_status_gentlequest=$?

check_completion_markers "hud.gentlequest.app"
marker_status_gentlequest=$?

echo ""
echo "=== hud.nucleusos.dev ==="
echo ""
check_dns_cname "hud.nucleusos.dev" "ghs.googlehosted.com."
dns_status_nucleusos=$?

check_nameservers "nucleusos.dev"
check_completion_markers "hud.nucleusos.dev"
marker_status_nucleusos=$?

echo ""
echo "=== Recent Activity ==="
echo ""
check_recent_events

echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

# Summary for hud.gentlequest.app
echo "hud.gentlequest.app:"
if [ $dns_status_gentlequest -eq 0 ] && [ $cr_status_gentlequest -eq 0 ]; then
    echo -e "  Status: ${GREEN}COMPLETE${NC} - DNS configured, certificate provisioned"
    echo "  Action: No work needed"
elif [ $dns_status_gentlequest -eq 0 ]; then
    echo -e "  Status: ${YELLOW}IN PROGRESS${NC} - DNS configured, waiting for certificate"
    echo "  Action: Wait 15-60 minutes for certificate provisioning"
else
    echo -e "  Status: ${RED}PENDING${NC} - DNS not configured"
    echo "  Action: Add CNAME in name.com DNS console"
fi

echo ""

# Summary for hud.nucleusos.dev
echo "hud.nucleusos.dev:"
if [ $dns_status_nucleusos -eq 0 ]; then
    echo -e "  Status: ${YELLOW}CONFIGURED${NC} - DNS exists but service returns 404"
    echo "  Action: Configure Google Sites or point to different target"
else
    echo -e "  Status: ${RED}PENDING${NC} - DNS not configured"
    echo "  Action: Add CNAME in Cloudflare or configure target service"
fi

echo ""
echo "======================================"
echo "Recommendation"
echo "======================================"
echo ""

if [ $dns_status_gentlequest -eq 0 ] && [ $cr_status_gentlequest -eq 0 ]; then
    echo -e "${GREEN}✅ hud.gentlequest.app is complete - no work needed${NC}"
elif [ $dns_status_gentlequest -eq 0 ]; then
    echo -e "${YELLOW}⏳ hud.gentlequest.app DNS configured - wait for certificate${NC}"
    echo "   Run this script again in 30 minutes to check certificate status"
else
    echo -e "${RED}❌ hud.gentlequest.app needs DNS configuration${NC}"
    echo "   See: .brain/artifacts/DNS_USER_ACTION_REQUIRED.md"
fi

echo ""

# Exit code based on overall status
if [ $dns_status_gentlequest -eq 0 ] && [ $cr_status_gentlequest -eq 0 ]; then
    exit 0  # Complete
elif [ $dns_status_gentlequest -eq 0 ]; then
    exit 2  # In progress
else
    exit 1  # Pending
fi
