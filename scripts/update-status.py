#!/usr/bin/env python3
# Regenerate human-readable status markdown from manifest

import json
import os
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".agent-manifest.json"
STATUS = ".agent-status.md"

def load_manifest():
    if not Path(MANIFEST).exists():
        return {"version": "1.0", "locks": {}, "agents": {}}
    with open(MANIFEST) as f:
        return json.load(f)

def parse_iso(ts):
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)

def main():
    manifest = load_manifest()
    now = datetime.now(timezone.utc)

    lines = [
        "# Agent Coordination Status",
        "",
        f"*Updated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
    ]

    locks = manifest.get("locks", {})
    if not locks:
        lines.extend(["## Active Locks", "", "*No active locks*"])
    else:
        lines.extend([f"## Active Locks ({len(locks)})", ""])
        lines.append("| File | Agent | Task | Acquired | Last Heartbeat | Status |")
        lines.append("|------|-------|------|----------|----------------|--------|")
        for file, lock in locks.items():
            hb = parse_iso(lock["heartbeat"])
            age = int((now - hb).total_seconds())
            status = "⚠️ STALE" if age > 300 else "✅ Active"
            lines.append(f"| {file} | {lock['agent_id']} | {lock['task']} | {lock['acquired']} | {lock['heartbeat']} | {status} |")

    lines.append("")
    lines.append("## Registered Agents")
    lines.append("")
    agents = manifest.get("agents", {})
    if not agents:
        lines.append("*No agents registered*")
    else:
        lines.append("| Agent | First Seen | Last Heartbeat | Status |")
        lines.append("|-------|------------|----------------|--------|")
        for agent_id, agent in agents.items():
            hb = parse_iso(agent["last_heartbeat"])
            age = int((now - hb).total_seconds())
            status = "⚠️ Inactive" if age > 600 else "✅ Active"
            lines.append(f"| {agent_id} | {agent['first_seen']} | {agent['last_heartbeat']} | {status} |")

    lines.extend([
        "",
        "---",
        "",
        "*This file is auto-generated. Do not edit manually — use the lock/unlock scripts.*"
    ])

    Path(STATUS).write_text("\n".join(lines))

if __name__ == "__main__":
    main()