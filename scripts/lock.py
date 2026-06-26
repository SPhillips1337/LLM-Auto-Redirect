#!/usr/bin/env python3
# Acquire lock on file(s) for current agent
# Usage: ./lock.py <file1> [file2...] "task description"

import json
import sys
import os
import socket
import random
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = ".agent-manifest.json"
SESSION_FILE = ".agent-session.json"

def get_agent_id():
    # Check for explicit agent ID via env var
    if "AGENT_ID" in os.environ:
        return os.environ["AGENT_ID"]
    
    # Check for persistent session file
    if Path(SESSION_FILE).exists():
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
                return data.get("agent_id")
        except Exception:
            pass
    
    # Generate new agent ID and save to session file
    agent_id = f"{socket.gethostname()}-{os.getpid()}-{random.randint(1000,9999)}"
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
    if len(sys.argv) < 3:
        print("Usage: lock.py <file1> [file2...] \"task description\"")
        sys.exit(1)

    task_desc = sys.argv[-1]
    files = [os.path.relpath(f) for f in sys.argv[1:-1]]

    manifest = load_manifest()
    agent_id = get_agent_id()
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    for file in files:
        if file in manifest["locks"]:
            locked_by = manifest["locks"][file]["agent_id"]
            if locked_by != agent_id:
                lock_task = manifest["locks"][file]["task"]
                lock_time = manifest["locks"][file]["acquired"]
                print(f"❌ LOCK FAILED: {file} is locked by {locked_by} since {lock_time}")
                print(f"   Task: {lock_task}")
                sys.exit(1)

        manifest["locks"][file] = {
            "agent_id": agent_id,
            "task": task_desc,
            "acquired": timestamp,
            "heartbeat": timestamp
        }
        manifest["agents"][agent_id] = {
            "name": agent_id,
            "first_seen": timestamp,
            "last_heartbeat": timestamp
        }
        print(f"✅ Locked: {file} (agent: {agent_id})")

    save_manifest(manifest)
    # Update human-readable status
    import subprocess
    script_dir = Path(__file__).parent
    subprocess.run([sys.executable, script_dir / "update-status.py"], capture_output=True)
    print(f"Task: {task_desc}")

if __name__ == "__main__":
    main()