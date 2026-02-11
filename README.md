# Experiential Memory System for OpenClaw

An arousal-based memory system that automatically scores, logs, and consolidates agent experiences.

## OpenClaw Core Patch Required

This system requires the `message:received` hook in OpenClaw. If your version doesn't have it:

```bash
# In your openclaw directory
git apply openclaw-hook.patch
npm run build
```

The patch adds `message:received` hook that fires on every incoming message with context:
- `body`, `rawBody` — Message content
- `senderId`, `channel`, `chatType` — Sender info
- `messageId`, `replyToId` — Message IDs
- `wasMentioned`, `workspaceDir` — Additional context

## What It Does

- **Automatic scoring** — Every incoming message is scored for arousal/importance (1-10)
- **Raw logging** — High-fidelity logs to `raw/<channel>/chats/<id>/YYYY/MM/DD.jsonl`
- **Memory flagging** — High-scoring messages flagged for consolidation
- **Debug tags** — Shows `[emoji score ctx:N⟳]` in responses for situational awareness
- **Satisfaction tracking** — Monitors user satisfaction patterns

## Quick Install

### 1. Copy scripts to your workspace

```bash
cp memory-system.py /path/to/your/workspace/scripts/
cp satisfaction-tracker.py /path/to/your/workspace/scripts/
chmod +x /path/to/your/workspace/scripts/*.py
```

### 2. Create required directories

```bash
mkdir -p /path/to/your/workspace/memory/_experimental
mkdir -p /path/to/your/workspace/raw
```

### 3. Enable the hook in OpenClaw config

Add to your `~/.openclaw/openclaw.json`:

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "memory-system": {
          "enabled": true
        }
      }
    }
  }
}
```

### 4. Add to AGENTS.md

Add this to your `AGENTS.md` to ensure the debug tag is rendered:

```markdown
### Debug Tag Display
**Include the debug tag in EVERY reply.** Read from:
\`\`\`
~/your-workspace/memory/_experimental/session-context.json → debugTag
\`\`\`
Format: `[emoji score ctx:N⟳]`
```

### 5. Restart OpenClaw

```bash
openclaw gateway restart
```

## How Scoring Works

Messages are scored on a 1-10 arousal scale:

| Score | Emoji | Meaning |
|-------|-------|---------|
| 1-2 | 💤 | Routine, low importance |
| 3-4 | 💭 | Normal conversation |
| 5-6 | 💡 | Interesting, worth noting |
| 7-8 | 🔥 | Important, flag for memory |
| 9-10 | 🚀 | Critical, must preserve |

## Files Created

```
workspace/
├── memory/
│   └── _experimental/
│       └── session-context.json    # Current session state + debug tag
├── raw/
│   └── <channel>/
│       └── chats/
│           └── <chat_id>/
│               └── YYYY/MM/DD.jsonl  # Raw message logs
└── scripts/
    ├── memory-system.py            # Core scoring + logging
    └── satisfaction-tracker.py     # User satisfaction tracking
```

## Configuration

Edit `memory-system.py` to customize:

- `AROUSAL_THRESHOLD` — Minimum score to flag for memory (default: 5.0)
- `RAW_LOG_DIR` — Where raw logs are stored
- `CONTEXT_FILE` — Location of session-context.json

## Satisfaction Tracking

Run daily summary:
```bash
python3 scripts/satisfaction-tracker.py daily-summary
```

Update learning document:
```bash
python3 scripts/satisfaction-tracker.py update-learning
```

## Cron Integration

Add to your OpenClaw cron for nightly consolidation:

```json
{
  "name": "nightly-memory-consolidation",
  "schedule": {"kind": "cron", "expr": "0 23 * * *"},
  "payload": {"kind": "agentTurn", "message": "Run nightly memory consolidation..."},
  "sessionTarget": "isolated"
}
```

## License

MIT — Use freely, improve freely, share freely.

## Credits

Developed for Zero (Tony's AI assistant) as part of the OpenClaw ecosystem.
