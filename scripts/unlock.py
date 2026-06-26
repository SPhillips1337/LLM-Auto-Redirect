#!/usr/bin/env python3
# Release lock on file(s) for current agent
# Usage: ./unlock.py <file1> [file2...]

import json
import sys
import os
import socket
import random
from pathlib import Path

MANIFEST = ".agent-manifest.json"
SESSION_FILE = ".agent-session.json"

def get_agent_id():
    if "AGENT_ID" in os.environ:
        return os.environ["AGENT_ID"]
    if Path(SESSION_FILE).exists():
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
                return data.get("agent_id")
        except Exception:
            pass
    agent_id = get_agent_id()
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({"agent_id": agent_id}, f)
    except Exception:
        pass
    return agent_id

def load_manifest():
    if not Path(MANIFEST).exists():
        return {"version": "1.0", "locks": {}, "agents": {}}
    with open(MANIFEST) as f:
        return json.load(f)

def save_manifest(data):
    with open(MANIFEST + ".tmp", "w") as f:
        json.dump(data, f, indent=2)
    os.replace(MANIFEST + ".tmp", MANIFEST)

def main():
    if len(sys.argv) < 2:
        print("Usage: unlock.py <file1> [file2...]")
        sys.exit(1)

    files = [os.path.relpath(f) for f in sys.argv[1:]]
    agent_id = get_agent_id()

    manifest = load_manifest()

    for file in files:
        if file not in manifest["locks"]:
            print(f"⚠️  Not locked: {file}")
            continue

        locked_by = manifest["locks"][file]["agent_id"]
        if locked_by != agent_id:
            print(f"❌ Cannot unlock: {file} is locked by {locked_by} (you are {agent_id})")
            print("   Use force-unlock.py if the other agent is dead")
            sys.exit(1)

        del manifest["locks"][file]
        print(f"🔓 Unlocked: {file}")

    # Clean up agent if no more locks
    remaining = sum(1 for v in manifest["locks"].values() if v["agent_id"] == agent_id)
    if remaining == 0:
        manifest["agents"].pop(agent_id, None)

    save_manifest(manifest)
    # Update human-readable status
    import subprocess
    script_dir = Path(__file__).parent
    subprocess.run([sys.executable, script_dir / "update-status.py"], capture_output=True)

if __name__ == "__main__":
    main()