#!/usr/bin/env python3
# Task board: create, list, claim, update, complete tasks
# Usage:
#   python3 tasks.py create "title" ["description"] [--files f1,f2,...] [--tag tag1,tag2,...]
#   python3 tasks.py list [--status pending|in_progress|blocked|completed|verified] [--agent AGENT_ID]
#   python3 tasks.py claim <task-id>
#   python3 tasks.py update <task-id> --status <status> [--note "note"] [--provenance verified|seeded|manual]
#   python3 tasks.py complete <task-id>
#   python3 tasks.py verify-complete <task-id>

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

TASKS_FILE = ".agent-tasks.json"
VALID_STATUSES = {"pending", "in_progress", "blocked", "completed", "verified"}


def get_agent_id() -> str:
    if "AGENT_ID" in os.environ:
        return os.environ["AGENT_ID"]
    session = Path(".agent-session.json")
    if session.exists():
        try:
            return json.loads(session.read_text()).get("agent_id")
        except Exception:
            pass
    import socket
    import random

    agent_id = f"{socket.gethostname()}-{os.getpid()}-{random.randint(1000, 9999)}"
    try:
        session.write_text(json.dumps({"agent_id": agent_id}))
    except Exception:
        pass
    return agent_id


def load_tasks() -> dict:
    if not Path(TASKS_FILE).exists():
        return {"version": "1.0", "tasks": {}}
    return json.loads(Path(TASKS_FILE).read_text())


def save_tasks(data: dict) -> None:
    Path(TASKS_FILE + ".tmp").write_text(json.dumps(data, indent=2))
    os.replace(TASKS_FILE + ".tmp", TASKS_FILE)


def transition_from(current: str, new: str) -> bool:
    if current == new:
        return True
    return new in {
        "pending": {"in_progress", "blocked", "completed"},
        "in_progress": {"pending", "blocked", "completed", "verified"},
        "blocked": {"pending", "in_progress"},
        "completed": {"pending", "in_progress"},
        "verified": {"pending", "in_progress"},
    }.get(current, set())


def create(args: list[str]) -> None:
    if not args:
        print('Usage: tasks.py create "title" ["description"] [--files f1,f2,...] [--tag tag1,tag2,...]')
        sys.exit(1)

    title = args[0]
    description = args[1] if len(args) > 1 else ""
    files: list[str] = []
    tags: list[str] = []
    i = 2
    while i < len(args):
        if args[i] == "--files" and i + 1 < len(args):
            files = [f.strip() for f in args[i + 1].split(",") if f.strip()]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tags = [t.strip() for t in args[i + 1].split(",") if t.strip()]
            i += 2
        else:
            i += 1

    data = load_tasks()
    task_id = f"task-{len(data['tasks']) + 1:03d}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    data["tasks"][task_id] = {
        "id": task_id,
        "title": title,
        "description": description,
        "status": "pending",
        "created": now,
        "updated": now,
        "assigned_to": None,
        "files": files,
        "tags": tags,
        "notes": [],
        "depends_on": [],
        "provenance": "seeded",
    }

    save_tasks(data)
    print(f"✅ Created task: {task_id} — {title}")


def list_tasks(args: list[str]) -> None:
    data = load_tasks()
    tasks = data.get("tasks", {})

    status_filter = None
    agent_filter = None
    i = 0
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status_filter = args[i + 1]
            i += 2
        elif args[i] == "--agent" and i + 1 < len(args):
            agent_filter = args[i + 1]
            i += 2
        else:
            i += 1

    filtered = []
    for tid, task in tasks.items():
        if status_filter and task["status"] != status_filter:
            continue
        if agent_filter and task["assigned_to"] != agent_filter:
            continue
        filtered.append(task)

    if not filtered:
        print("📭 No tasks match filter")
        return

    by_status = {}
    for t in filtered:
        by_status.setdefault(t["status"], []).append(t)

    print("=" * 80)
    print("  TASK BOARD")
    print("=" * 80)
    for status in ["pending", "in_progress", "blocked", "completed", "verified"]:
        items = by_status.get(status, [])
        if not items:
            continue
        emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "blocked": "🚫",
            "completed": "✅",
            "verified": "🧪",
        }.get(status, "❓")
        print(f"\n{emoji} {status.upper()} ({len(items)})")
        print("-" * 80)
        for t in items:
            agent = t["assigned_to"] or "unassigned"
            files = ", ".join(t["files"]) if t["files"] else "none"
            prov = t.get("provenance", "")
            prov_label = f" [{prov}]" if prov else ""
            print(f"  {t['id']}: {t['title']}{prov_label}")
            print(f"    Agent: {agent}")
            print(f"    Files: {files}")
            if t["tags"]:
                print(f"    Tags: {', '.join(t['tags'])}")
            if t["description"]:
                print(f"    Desc: {t['description'][:100]}")
            if t["notes"]:
                print(f"    Last note: {t['notes'][-1]['text'][:80]}")

    print()
    print("=" * 80)
    print(f"Board: {TASKS_FILE}")


def claim(args: list[str]) -> None:
    if not args:
        print("Usage: tasks.py claim <task-id>")
        sys.exit(1)
    task_id = args[0]
    agent_id = get_agent_id()

    data = load_tasks()
    if task_id not in data["tasks"]:
        print(f"❌ Task not found: {task_id}")
        sys.exit(1)

    task = data["tasks"][task_id]
    if task["status"] == "completed":
        print(f"❌ Task already finalized: {task_id}")
        sys.exit(1)
    if task["status"] == "verified":
        print(f"❌ Task already verified: {task_id}")
        sys.exit(1)
    if task["status"] == "in_progress" and task["assigned_to"] != agent_id:
        print(f"❌ Task in progress by {task['assigned_to']}: {task_id}")
        sys.exit(1)

    lock_notes = []
    if task.get("files"):
        import subprocess

        script_dir = Path(__file__).parent
        for file_path in task["files"]:
            result = subprocess.run(
                [
                    sys.executable,
                    script_dir / "lock.py",
                    file_path,
                    f"task {task_id}: {task['title']}",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                lock_notes.append(f"locked {file_path}")
            else:
                lock_notes.append(
                    f"lock failed for {file_path}: {result.stderr.strip() or result.stdout.strip()}"
                )

    task["status"] = "in_progress"
    task["assigned_to"] = agent_id
    task["updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if lock_notes:
        task.setdefault("notes", []).append(
            {
                "agent": agent_id,
                "text": "Lock acquisition: " + "; ".join(lock_notes),
                "timestamp": task["updated"],
            }
        )

    save_tasks(data)
    print(f"✅ Claimed task: {task_id} — {task['title']}")
    print(f"   Agent: {agent_id}")
    for note in lock_notes:
        print(f"   {note}")


def update_task(args: list[str]) -> None:
    if len(args) < 2:
        print('Usage: tasks.py update <task-id> --status <status> [--note "note"] [--provenance verified|seeded|manual]')
        sys.exit(1)

    task_id = args[0]
    status = None
    note = None
    provenance = None
    i = 1
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]
            i += 2
        elif args[i] == "--note" and i + 1 < len(args):
            note = args[i + 1]
            i += 2
        elif args[i] == "--provenance" and i + 1 < len(args):
            provenance = args[i + 1]
            i += 2
        else:
            i += 1

    if not status:
        print("❌ --status is required")
        sys.exit(1)

    if status not in VALID_STATUSES:
        print(f"❌ Invalid status. Use: {', '.join(sorted(VALID_STATUSES))}")
        sys.exit(1)

    data = load_tasks()
    if task_id not in data["tasks"]:
        print(f"❌ Task not found: {task_id}")
        sys.exit(1)

    task = data["tasks"][task_id]
    agent_id = get_agent_id()
    current = task.get("status", "pending")
    if not transition_from(current, status):
        print(f"❌ Invalid status transition: {current} -> {status}")
        sys.exit(1)

    if status == "completed":
        missing = [
            fp
            for fp in task.get("files", [])
            if not Path(fp).exists() or Path(fp).stat().st_size == 0
        ]
        if missing:
            print(
                f"❌ Cannot complete {task_id}: missing or empty files: {', '.join(missing)}"
            )
            sys.exit(1)
        provenance = provenance or "manual"
        task["assigned_to"] = None

    task["status"] = status
    task["updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if provenance:
        task["provenance"] = provenance
    if note:
        task["notes"].append(
            {"agent": agent_id, "text": note, "timestamp": task["updated"]}
        )

    save_tasks(data)
    print(f"✅ Updated {task_id}: {status}")
    if provenance:
        print(f"   Provenance: {provenance}")
    if note:
        print(f"   Note: {note}")


def complete(args: list[str]) -> None:
    if not args:
        print("Usage: tasks.py complete <task-id>")
        sys.exit(1)
    update_task([args[0], "--status", "completed"])


def complete_with_verify(args: list[str]) -> None:
    if not args:
        print("Usage: tasks.py verify-complete <task-id>")
        sys.exit(1)
    task_id = args[0]
    data = load_tasks()
    if task_id not in data["tasks"]:
        print(f"❌ Task not found: {task_id}")
        sys.exit(1)
    task = data["tasks"][task_id]
    missing = [
        fp for fp in task.get("files", []) if not Path(fp).exists() or Path(fp).stat().st_size == 0
    ]
    if missing:
        print(
            f"❌ Cannot verify-complete {task_id}: missing or empty files: {', '.join(missing)}"
        )
        sys.exit(1)
    
    print("⚠️  WARNING: verify-complete only checks file existence and non-emptiness.")
    print("   Please ensure you have manually run compilers (e.g. tsc), builds, and test suites (e.g. pytest).")
    
    update_task([task_id, "--status", "verified", "--provenance", "verified"])


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: tasks.py <create|list|claim|update|complete|verify-complete> ...")
        sys.exit(1)

    cmd = sys.argv[1]
    rest = sys.argv[2:]

    if cmd == "create":
        create(rest)
    elif cmd == "list":
        list_tasks(rest)
    elif cmd == "claim":
        claim(rest)
    elif cmd == "update":
        update_task(rest)
    elif cmd == "complete":
        complete(rest)
    elif cmd == "verify-complete":
        complete_with_verify(rest)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
