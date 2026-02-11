#!/bin/bash
# Experiential Memory System Installer for OpenClaw

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Experiential Memory System...${NC}"

# Get workspace directory
if [ -z "$1" ]; then
    echo "Usage: ./install.sh /path/to/workspace"
    echo "Example: ./install.sh ~/clawd"
    exit 1
fi

WORKSPACE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create directories
echo "Creating directories..."
mkdir -p "$WORKSPACE/scripts"
mkdir -p "$WORKSPACE/memory/_experimental"
mkdir -p "$WORKSPACE/raw"

# Copy scripts
echo "Copying scripts..."
cp "$SCRIPT_DIR/memory-system.py" "$WORKSPACE/scripts/"
cp "$SCRIPT_DIR/satisfaction-tracker.py" "$WORKSPACE/scripts/"
chmod +x "$WORKSPACE/scripts/memory-system.py"
chmod +x "$WORKSPACE/scripts/satisfaction-tracker.py"

# Initialize session context
echo "Initializing session context..."
cat > "$WORKSPACE/memory/_experimental/session-context.json" << 'EOF'
{
  "lastMessage": {
    "timestamp": 0,
    "score": 0,
    "emoji": "💭",
    "flags": [],
    "saved": false
  },
  "sessionContextCount": 0,
  "debugTag": "[💭 0.0 ctx:0⟳]"
}
EOF

echo -e "${GREEN}✓ Scripts installed to $WORKSPACE/scripts/${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Add hook config to ~/.openclaw/openclaw.json:"
echo '   "hooks": { "internal": { "enabled": true, "entries": { "memory-system": { "enabled": true } } } }'
echo ""
echo "2. Add debug tag instruction to your AGENTS.md"
echo ""
echo "3. Restart OpenClaw: openclaw gateway restart"
echo ""
echo -e "${GREEN}Done!${NC}"
