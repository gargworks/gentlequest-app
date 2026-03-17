#!/bin/bash
# Nucleus Telemetry Toggle - Easy on/off switch for dev environment

SHELL_RC="$HOME/.zshrc"
ENV_VAR="NUCLEUS_ANON_TELEMETRY"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check current status
check_status() {
    if grep -q "export ${ENV_VAR}=false" "$SHELL_RC" 2>/dev/null; then
        echo "disabled"
    elif [ "${!ENV_VAR}" = "false" ]; then
        echo "disabled"
    else
        echo "enabled"
    fi
}

# Show current status
show_status() {
    STATUS=$(check_status)
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 NUCLEUS TELEMETRY STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    if [ "$STATUS" = "enabled" ]; then
        echo -e "  Status: ${GREEN}ENABLED${NC} ✅"
        echo "  Your commands are being tracked anonymously"
    else
        echo -e "  Status: ${RED}DISABLED${NC} ⛔"
        echo "  Your commands are NOT being tracked"
    fi
    echo ""
    echo "  Current session: ${!ENV_VAR:-not set}"
    echo "  Shell config: $SHELL_RC"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Disable telemetry
disable() {
    echo ""
    echo "🛑 Disabling telemetry..."
    
    # Add to shell config if not already there
    if ! grep -q "export ${ENV_VAR}=false" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Nucleus Telemetry (disabled for dev)" >> "$SHELL_RC"
        echo "export ${ENV_VAR}=false" >> "$SHELL_RC"
        echo "  ✅ Added to $SHELL_RC"
    else
        echo "  ℹ️  Already in $SHELL_RC"
    fi
    
    # Set for current session
    export NUCLEUS_ANON_TELEMETRY=false
    echo "  ✅ Disabled for current session"
    echo ""
    echo -e "${GREEN}Telemetry is now OFF${NC}"
    echo ""
    echo "💡 Tip: Open a new terminal or run 'source ~/.zshrc' to apply"
    echo ""
}

# Enable telemetry
enable() {
    echo ""
    echo "✅ Enabling telemetry..."
    
    # Remove from shell config
    if grep -q "export ${ENV_VAR}=false" "$SHELL_RC" 2>/dev/null; then
        # Remove the line and the comment above it
        sed -i.bak '/# Nucleus Telemetry/d' "$SHELL_RC"
        sed -i.bak "/export ${ENV_VAR}=false/d" "$SHELL_RC"
        rm -f "${SHELL_RC}.bak"
        echo "  ✅ Removed from $SHELL_RC"
    else
        echo "  ℹ️  Not in $SHELL_RC"
    fi
    
    # Unset for current session
    unset NUCLEUS_ANON_TELEMETRY
    echo "  ✅ Enabled for current session"
    echo ""
    echo -e "${GREEN}Telemetry is now ON${NC}"
    echo ""
    echo "💡 Tip: Open a new terminal or run 'source ~/.zshrc' to apply"
    echo ""
}

# Main
case "${1:-status}" in
    on|enable)
        enable
        ;;
    off|disable)
        disable
        ;;
    status)
        show_status
        ;;
    toggle)
        STATUS=$(check_status)
        if [ "$STATUS" = "enabled" ]; then
            disable
        else
            enable
        fi
        ;;
    *)
        echo ""
        echo "Usage: $0 {on|off|status|toggle}"
        echo ""
        echo "Commands:"
        echo "  on, enable   - Enable telemetry"
        echo "  off, disable - Disable telemetry"
        echo "  status       - Show current status (default)"
        echo "  toggle       - Switch between on/off"
        echo ""
        exit 1
        ;;
esac
