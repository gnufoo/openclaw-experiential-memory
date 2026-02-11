#!/usr/bin/env python3
"""
User Satisfaction & Interest Tracking System
Records emotional signals, analyzes patterns, generates behavioral insights
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

WORKSPACE = Path("/home/gnufoo/clawd")
TRACKER_FILE = WORKSPACE / "memory" / "satisfaction-tracker.json"
INSIGHTS_DIR = WORKSPACE / "memory" / "satisfaction-insights"
LEARNING_FILE = WORKSPACE / "LEARNING.md"

# Ensure directories exist
INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

def load_tracker() -> Dict[str, Any]:
    """Load or create satisfaction tracker"""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {
        "incidents": [],
        "patterns": {},
        "last_summary": None
    }

def save_tracker(data: Dict[str, Any]):
    """Save tracker data"""
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def detect_signal(message: str) -> Optional[str]:
    """Detect satisfaction signals in user messages"""
    message_lower = message.lower()
    
    # Negative signals
    negative_patterns = [
        "not satisfied", "unsatisfying", "disappointed", "frustrated",
        "that's not what i", "you don't understand", "no that's wrong",
        "i'm worried about your ability", "concerning", "this is a problem",
        "you missed", "you forgot", "you didn't", "why didn't you"
    ]
    
    # Positive signals
    positive_patterns = [
        "perfect", "exactly", "great", "excellent", "love it",
        "that's what i wanted", "super interested", "this is good",
        "nice", "well done", "impressive", "smart"
    ]
    
    # Interest signals
    interest_patterns = [
        "interesting", "tell me more", "i want to know",
        "curious about", "what about", "can you explain"
    ]
    
    for pattern in negative_patterns:
        if pattern in message_lower:
            return "negative"
    
    for pattern in positive_patterns:
        if pattern in message_lower:
            return "positive"
    
    for pattern in interest_patterns:
        if pattern in message_lower:
            return "interested"
    
    return None

def record_incident(
    signal: str,
    context: str,
    user_message: str,
    my_response: str,
    analysis: Optional[str] = None
) -> str:
    """Record a satisfaction incident"""
    tracker = load_tracker()
    
    timestamp = datetime.utcnow()
    incident = {
        "id": timestamp.strftime("%Y%m%d_%H%M%S"),
        "timestamp": timestamp.isoformat() + "Z",
        "signal": signal,  # negative, positive, interested
        "context": context,
        "user_message": user_message[:200],  # truncate
        "my_response": my_response[:200],
        "analysis": analysis or "Pending analysis"
    }
    
    tracker["incidents"].append(incident)
    save_tracker(tracker)
    
    return incident["id"]

def analyze_patterns(since_days: int = 7) -> Dict[str, Any]:
    """Analyze satisfaction patterns over time"""
    tracker = load_tracker()
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    
    recent = [
        inc for inc in tracker["incidents"]
        if datetime.fromisoformat(inc["timestamp"].replace("Z", ""))
        >= cutoff
    ]
    
    if not recent:
        return {"message": "No incidents in the specified period"}
    
    # Count signals
    signal_counts = {}
    for inc in recent:
        signal = inc["signal"]
        signal_counts[signal] = signal_counts.get(signal, 0) + 1
    
    # Extract common themes
    contexts = [inc["context"] for inc in recent]
    
    # Calculate satisfaction ratio
    total = len(recent)
    positive = signal_counts.get("positive", 0)
    negative = signal_counts.get("negative", 0)
    
    satisfaction_ratio = positive / total if total > 0 else 0
    concern_ratio = negative / total if total > 0 else 0
    
    return {
        "period": f"Last {since_days} days",
        "total_incidents": total,
        "signal_breakdown": signal_counts,
        "satisfaction_ratio": round(satisfaction_ratio, 2),
        "concern_ratio": round(concern_ratio, 2),
        "common_contexts": list(set(contexts)),
        "recent_incidents": recent[-5:]  # Last 5
    }

def generate_daily_summary() -> str:
    """Generate daily satisfaction summary"""
    tracker = load_tracker()
    today = datetime.utcnow().date()
    
    # Get today's incidents
    today_incidents = [
        inc for inc in tracker["incidents"]
        if datetime.fromisoformat(inc["timestamp"].replace("Z", "")).date()
        == today
    ]
    
    if not today_incidents:
        return "No satisfaction incidents recorded today."
    
    # Analyze patterns
    patterns = analyze_patterns(since_days=7)
    
    # Build summary
    summary_lines = [
        f"# Satisfaction Summary - {today.isoformat()}",
        "",
        f"**Today's Incidents:** {len(today_incidents)}",
        f"**7-Day Satisfaction Ratio:** {patterns.get('satisfaction_ratio', 0):.0%}",
        f"**7-Day Concern Ratio:** {patterns.get('concern_ratio', 0):.0%}",
        "",
        "## Today's Incidents",
        ""
    ]
    
    for inc in today_incidents:
        summary_lines.extend([
            f"### {inc['timestamp']} - {inc['signal'].upper()}",
            f"**Context:** {inc['context']}",
            f"**User:** {inc['user_message'][:100]}...",
            f"**Analysis:** {inc['analysis']}",
            ""
        ])
    
    summary_lines.extend([
        "## Key Learnings",
        ""
    ])
    
    # Extract learnings
    negative_incidents = [inc for inc in today_incidents if inc["signal"] == "negative"]
    if negative_incidents:
        summary_lines.append("**Areas for Improvement:**")
        for inc in negative_incidents:
            summary_lines.append(f"- {inc['context']}: {inc['analysis']}")
        summary_lines.append("")
    
    positive_incidents = [inc for inc in today_incidents if inc["signal"] == "positive"]
    if positive_incidents:
        summary_lines.append("**What Worked Well:**")
        for inc in positive_incidents:
            summary_lines.append(f"- {inc['context']}")
        summary_lines.append("")
    
    summary_text = "\n".join(summary_lines)
    
    # Save daily summary
    summary_file = INSIGHTS_DIR / f"{today.isoformat()}_daily_summary.md"
    with open(summary_file, 'w') as f:
        f.write(summary_text)
    
    # Update tracker
    tracker["last_summary"] = today.isoformat()
    save_tracker(tracker)
    
    return str(summary_file)

def update_learning_doc():
    """Update LEARNING.md with latest insights"""
    tracker = load_tracker()
    patterns = analyze_patterns(since_days=30)
    
    # Build learning document
    lines = [
        "# LEARNING.md - Behavioral Insights",
        "",
        "This file contains automatically-generated insights from user satisfaction tracking.",
        "It informs my behavioral adjustments and response patterns.",
        "",
        f"**Last Updated:** {datetime.utcnow().isoformat()}Z",
        f"**Data Period:** Last 30 days",
        "",
        "---",
        "",
        "## Satisfaction Metrics",
        "",
        f"- **Total Interactions Analyzed:** {patterns.get('total_incidents', 0)}",
        f"- **Satisfaction Ratio:** {patterns.get('satisfaction_ratio', 0):.0%}",
        f"- **Concern Ratio:** {patterns.get('concern_ratio', 0):.0%}",
        "",
        "## Behavioral Patterns",
        ""
    ]
    
    # Extract patterns from recent negative incidents
    negative_incidents = [
        inc for inc in tracker["incidents"][-50:]  # Last 50
        if inc["signal"] == "negative"
    ]
    
    if negative_incidents:
        lines.extend([
            "### Things That Cause Dissatisfaction",
            ""
        ])
        
        contexts = {}
        for inc in negative_incidents:
            ctx = inc["context"]
            contexts[ctx] = contexts.get(ctx, 0) + 1
        
        sorted_contexts = sorted(contexts.items(), key=lambda x: x[1], reverse=True)
        for ctx, count in sorted_contexts[:10]:  # Top 10
            lines.append(f"- **{ctx}** (occurred {count}x)")
        lines.append("")
    
    # Extract positive patterns
    positive_incidents = [
        inc for inc in tracker["incidents"][-50:]
        if inc["signal"] == "positive"
    ]
    
    if positive_incidents:
        lines.extend([
            "### Things That Work Well",
            ""
        ])
        
        contexts = {}
        for inc in positive_incidents:
            ctx = inc["context"]
            contexts[ctx] = contexts.get(ctx, 0) + 1
        
        sorted_contexts = sorted(contexts.items(), key=lambda x: x[1], reverse=True)
        for ctx, count in sorted_contexts[:10]:
            lines.append(f"- **{ctx}** (occurred {count}x)")
        lines.append("")
    
    lines.extend([
        "## Actionable Insights",
        "",
        "Based on the data above, here are the key behavioral adjustments:",
        ""
    ])
    
    # Generate insights
    if patterns.get('concern_ratio', 0) > 0.3:
        lines.append("⚠️ **HIGH CONCERN RATIO** - Review negative incidents and adjust behavior")
    
    if negative_incidents:
        top_concern = sorted(
            contexts.items(), key=lambda x: x[1], reverse=True
        )[0][0] if contexts else "Unknown"
        lines.append(f"🔴 **Primary Concern Area:** {top_concern}")
    
    if positive_incidents:
        top_success = sorted(
            [(inc["context"], 1) for inc in positive_incidents],
            key=lambda x: x[1],
            reverse=True
        )[0][0] if positive_incidents else "Unknown"
        lines.append(f"✅ **Keep Doing:** {top_success}")
    
    lines.extend([
        "",
        "---",
        "",
        "**Note:** This file is auto-generated by `scripts/satisfaction-tracker.py`.",
        "It is updated daily by cron and read by the agent on startup."
    ])
    
    # Write to LEARNING.md
    with open(LEARNING_FILE, 'w') as f:
        f.write("\n".join(lines))
    
    return str(LEARNING_FILE)

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: satisfaction-tracker.py <command> [args]")
        print("Commands:")
        print("  record <signal> <context> <user_msg> <my_response> [analysis]")
        print("  analyze [days]")
        print("  daily-summary")
        print("  update-learning")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "record":
        if len(sys.argv) < 6:
            print("Usage: record <signal> <context> <user_msg> <my_response> [analysis]")
            sys.exit(1)
        
        signal = sys.argv[2]
        context = sys.argv[3]
        user_msg = sys.argv[4]
        my_response = sys.argv[5]
        analysis = sys.argv[6] if len(sys.argv) > 6 else None
        
        incident_id = record_incident(signal, context, user_msg, my_response, analysis)
        print(f"Recorded incident: {incident_id}")
    
    elif command == "analyze":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        patterns = analyze_patterns(since_days=days)
        print(json.dumps(patterns, indent=2))
    
    elif command == "daily-summary":
        summary_file = generate_daily_summary()
        print(f"Daily summary saved: {summary_file}")
    
    elif command == "update-learning":
        learning_file = update_learning_doc()
        print(f"Learning document updated: {learning_file}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
