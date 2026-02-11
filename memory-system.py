#!/usr/bin/env python3
"""
Memory System - Unified interface for experiential memory.

Wires together all components:
- Arousal encoding
- Prediction error
- Session context
- Memory recall (with reconsolidation)
- Auto-save on high scores
- Forgetting recommendations

Usage:
  python3 scripts/memory-system.py boot           # Run at session start
  python3 scripts/memory-system.py process "msg"  # Process a message
  python3 scripts/memory-system.py save "content" # Save with scoring
  python3 scripts/memory-system.py search "query" # Search with reconsolidation
  python3 scripts/memory-system.py status         # System status
  python3 scripts/memory-system.py daily          # Run daily consolidation
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

CLAWD_ROOT = Path('/home/gnufoo/clawd')
SCRIPTS_DIR = CLAWD_ROOT / 'scripts'
MEMORY_DIR = CLAWD_ROOT / 'memory'
EXPERIMENTAL_DIR = MEMORY_DIR / '_experimental'
STATE_FILE = EXPERIMENTAL_DIR / 'system-state.json'

# Thresholds
AUTO_SAVE_THRESHOLD = 5.0  # Score above this triggers auto-save consideration
HIGHLIGHT_THRESHOLD = 7.0  # Score above this is highlighted as important


def load_state() -> Dict:
    """Load system state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        'session_start': None,
        'messages_processed': 0,
        'high_scores': [],
        'last_consolidation': None
    }


def save_state(state: Dict):
    """Save system state."""
    EXPERIMENTAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def run_script(script: str, args: list = None) -> Dict:
    """Run a memory system script."""
    cmd = ['python3', str(SCRIPTS_DIR / script)]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(CLAWD_ROOT))
    return {
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr
    }


def boot() -> Dict:
    """Boot the memory system for a new session."""
    now = datetime.utcnow().isoformat() + 'Z'
    
    results = {
        'timestamp': now,
        'actions': []
    }
    
    # 1. Sync context from session
    sync_result = run_script('auto-context.py', ['sync', '--last', '15'])
    results['actions'].append({
        'action': 'sync_context',
        'success': sync_result['success'],
        'output': sync_result['stdout'][:200] if sync_result['success'] else sync_result['stderr'][:200]
    })
    
    # 2. Check for pending forgetting actions
    forget_result = run_script('../projects/experiential-memory/forgetting.py', ['scan', '--json'])
    if forget_result['success']:
        try:
            scan_data = json.loads(forget_result['stdout'])
            forget_candidates = [s for s in scan_data if s.get('recommendation') != 'KEEP']
            results['actions'].append({
                'action': 'forgetting_scan',
                'candidates': len(forget_candidates)
            })
        except:
            pass
    
    # 3. Update state
    state = load_state()
    state['session_start'] = now
    state['messages_processed'] = 0
    state['high_scores'] = []
    save_state(state)
    
    results['status'] = 'ready'
    return results


def process_message(message: str) -> Dict:
    """Process a message through the full pipeline."""
    now = datetime.utcnow().isoformat() + 'Z'
    
    # 1. Analyze with auto-context
    analyze_result = run_script('auto-context.py', ['analyze', message, '--json'])
    
    if not analyze_result['success']:
        return {'success': False, 'error': analyze_result['stderr']}
    
    try:
        analysis = json.loads(analyze_result['stdout'])
    except:
        # Parse from non-JSON output
        analysis = {'combined': 2.0, 'arousal': 1.5, 'pe': 0.3, 'surprise': 'mild'}
    
    combined = analysis.get('combined', 2.0)
    
    # 2. Update state
    state = load_state()
    state['messages_processed'] = state.get('messages_processed', 0) + 1
    
    result = {
        'timestamp': now,
        'message_preview': message[:100],
        'score': combined,
        'analysis': analysis,
        'actions': []
    }
    
    # 3. Check if this should be saved
    if combined >= AUTO_SAVE_THRESHOLD:
        result['flag'] = 'SIGNIFICANT'
        result['actions'].append('Consider saving to memory')
        state['high_scores'].append({
            'timestamp': now,
            'score': combined,
            'preview': message[:100]
        })
        # Keep only last 10 high scores
        state['high_scores'] = state['high_scores'][-10:]
    
    if combined >= HIGHLIGHT_THRESHOLD:
        result['flag'] = 'IMPORTANT'
        result['actions'].append('High importance - strongly recommend saving')
    
    save_state(state)
    
    # 4. Format debug string
    emoji = "🔥" if combined >= 7 else "⚡" if combined >= 5 else "📊" if combined >= 3 else "💤"
    surprise_mark = {'moderate': '?', 'high': '!', 'shocking': '‼️'}.get(analysis.get('surprise', ''), '')
    context_count = analysis.get('context_size', 0)
    
    result['debug'] = f"[{emoji} {combined:.1f}{surprise_mark} ctx:{context_count}⟳]"
    
    # 5. Add fields for hook integration
    result['emoji'] = emoji
    result['context_count'] = context_count
    result['flags'] = []
    if combined >= HIGHLIGHT_THRESHOLD:
        result['flags'].append('IMPORTANT')
    elif combined >= AUTO_SAVE_THRESHOLD:
        result['flags'].append('SIGNIFICANT')
    result['saved'] = False  # Hook can trigger save if needed
    
    return result


def save_memory(content: str, title: str = None, category: str = None) -> Dict:
    """Save content to memory with automatic scoring."""
    now = datetime.utcnow()
    date_str = now.strftime('%Y-%m-%d')
    
    # Determine file path
    if category:
        file_path = f"memory/{category}/{title or 'entry'}.md"
    else:
        file_path = f"memory/{date_str}.md"
    
    # Run memory-write with scoring
    args = [
        '--file', file_path,
        '--content', content,
        '--append'
    ]
    if title:
        args.extend(['--title', title])
    
    result = run_script('memory-write.py', args)
    
    return {
        'success': result['success'],
        'file': file_path,
        'output': result['stdout'] if result['success'] else result['stderr']
    }


def search_memory(query: str, apply_reconsolidation: bool = True) -> Dict:
    """Search memories with reconsolidation."""
    args = [query, '--top', '5']
    if apply_reconsolidation:
        args.append('--apply')
    
    result = run_script('memory-recall.py', args)
    
    return {
        'success': result['success'],
        'results': result['stdout'] if result['success'] else result['stderr']
    }


def run_daily() -> Dict:
    """Run daily consolidation."""
    results = {'actions': []}
    
    # 1. Run nightly consolidation
    consol_result = run_script('nightly-consolidate.py', [])
    results['actions'].append({
        'action': 'consolidation',
        'success': consol_result['success'],
        'output': consol_result['stdout'][:500]
    })
    
    # 2. Run forgetting scan
    forget_result = run_script('../projects/experiential-memory/forgetting.py', ['scan'])
    results['actions'].append({
        'action': 'forgetting_scan',
        'output': forget_result['stdout'][:500]
    })
    
    # 3. Update state
    state = load_state()
    state['last_consolidation'] = datetime.utcnow().isoformat() + 'Z'
    save_state(state)
    
    return results


def show_status() -> Dict:
    """Show system status."""
    state = load_state()
    
    # Count memories
    memory_count = sum(1 for _ in MEMORY_DIR.rglob('*.md') if '_experimental' not in str(_))
    shadow_count = sum(1 for _ in (EXPERIMENTAL_DIR / 'shadow').rglob('*.md')) if (EXPERIMENTAL_DIR / 'shadow').exists() else 0
    
    # Check context
    context_file = CLAWD_ROOT / '.session-context.json'
    context_count = 0
    if context_file.exists():
        with open(context_file) as f:
            ctx = json.load(f)
            context_count = len(ctx.get('messages', []))
    
    return {
        'session_start': state.get('session_start'),
        'messages_processed': state.get('messages_processed', 0),
        'high_scores_this_session': len(state.get('high_scores', [])),
        'last_consolidation': state.get('last_consolidation'),
        'memory_files': memory_count,
        'shadow_files': shadow_count,
        'context_messages': context_count,
        'thresholds': {
            'auto_save': AUTO_SAVE_THRESHOLD,
            'highlight': HIGHLIGHT_THRESHOLD
        }
    }


def format_status(status: Dict) -> str:
    """Format status for display."""
    lines = []
    lines.append("# Memory System Status")
    lines.append("=" * 50)
    lines.append(f"Session start: {status['session_start'] or 'Not booted'}")
    lines.append(f"Messages processed: {status['messages_processed']}")
    lines.append(f"High scores this session: {status['high_scores_this_session']}")
    lines.append(f"Last consolidation: {status['last_consolidation'] or 'Never'}")
    lines.append(f"")
    lines.append(f"Memory files: {status['memory_files']}")
    lines.append(f"Shadow files: {status['shadow_files']}")
    lines.append(f"Context messages: {status['context_messages']}")
    lines.append(f"")
    lines.append(f"Thresholds:")
    lines.append(f"  Auto-save: {status['thresholds']['auto_save']}")
    lines.append(f"  Highlight: {status['thresholds']['highlight']}")
    return '\n'.join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified memory system')
    parser.add_argument('action', choices=['boot', 'process', 'save', 'search', 'status', 'daily'])
    parser.add_argument('arg', nargs='?', help='Message, content, or query')
    parser.add_argument('--title', '-t', type=str, help='Title for save')
    parser.add_argument('--category', '-c', type=str, help='Category for save')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    
    args = parser.parse_args()
    
    if args.action == 'boot':
        result = boot()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("🚀 Memory System Booted")
            for action in result['actions']:
                status = "✅" if action.get('success', True) else "❌"
                print(f"   {status} {action['action']}")
            print(f"\nStatus: {result['status']}")
    
    elif args.action == 'process':
        if not args.arg:
            print("Error: message required")
            sys.exit(1)
        result = process_message(args.arg)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Debug: {result['debug']}")
            if result.get('flag'):
                print(f"⚠️ {result['flag']}: {', '.join(result['actions'])}")
    
    elif args.action == 'save':
        if not args.arg:
            print("Error: content required")
            sys.exit(1)
        result = save_memory(args.arg, args.title, args.category)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['success']:
                print(f"✅ Saved to {result['file']}")
            else:
                print(f"❌ Failed: {result['output']}")
    
    elif args.action == 'search':
        if not args.arg:
            print("Error: query required")
            sys.exit(1)
        result = search_memory(args.arg)
        print(result['results'])
    
    elif args.action == 'status':
        status = show_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(format_status(status))
    
    elif args.action == 'daily':
        result = run_daily()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("🌙 Daily Consolidation")
            for action in result['actions']:
                print(f"\n### {action['action']}")
                print(action.get('output', '')[:300])


if __name__ == "__main__":
    main()
