# HERMES.md — LLM Auto Redirect Agent Guide

## Role

You are operating inside a coordinated task-based swarm building the LLM Auto Redirect WordPress plugin. Treat this repo as a shared workspace with explicit coordination rules.

## Operating rules

- **Branch Protocol**: Use branches for clean merges and reviewable commits if executing as part of an upstream flow.
- **Locking Protocol**: Summarize current locks using `python3 scripts/status.py` before modifying project files.
- **Zero Conflict Resolution**: If merge conflicts occur during branch operations, stop immediately and report them; do not attempt to silently resolve.

## Expectations

- **Code/Doc Sync**: Any protocol or feature change must update the corresponding `CONTEXT.md` and/or ADRs in the same commit.
- **Durable Decisions**: Significant architectural decisions must be recorded in `docs/adr/`.
- **Reference Material**: Research notes go in `research/`, keeping `docs/` focused on project specs.

## Workflow

1. **Check Task Board**:
   ```bash
   python3 scripts/tasks.py list
   ```
2. **Claim a Task**:
   ```bash
   python3 scripts/tasks.py claim <task-id>
   ```
3. **Lock Files**:
   ```bash
   python3 scripts/lock.py <file-path> "Reason for modification"
   ```
4. **Complete Work & Verify**:
   Run validation checks:
   ```bash
   python3 scripts/bootstrap-validate.py
   python3 scripts/tasks.py verify-complete <task-id>
   ```
5. **Release Locks**:
   ```bash
   python3 scripts/unlock.py <file-path>
   ```

## Quick reference

```bash
# Task board
python3 scripts/tasks.py list

# Claim
python3 scripts/tasks.py claim task-001

# Lock file
python3 scripts/lock.py LLM_Auto_Redirect.php "Updating API call parameters"

# Unlock file
python3 scripts/unlock.py LLM_Auto_Redirect.php
```
