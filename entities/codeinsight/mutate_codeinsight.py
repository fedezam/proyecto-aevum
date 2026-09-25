Here is the translated content of `/workspaces/ler-universe17/LER/entities/codeinsight/mutate_codeinsight.py`:

```python
#!/usr/bin/env python3
# [GL30-O] Executor for AuditorLER to safely apply CodeInsight self-fixes.

import json, re, os, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../LER/
PLAN_PATH = ROOT / "entities" / "codeinsight" / "auditor_plan_apply_codeinsight.json"
TARGET = ROOT / "entities" / "codeinsight"
SNAPS = TARGET / "storage" / "snapshots"
SNAPS.mkdir(parents=True, exist_ok=True)

def backup(path: Path):
    if path.exists():
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        dst = SNAPS / f"{path.name}.{timestamp}.bak"
        try:
            shutil.copy(path, dst)
        except Exception as e:
            print(f"[GLD] Backup failed for {path}: {e}")

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, s: str):
    backup(p)
    p.write_text(s, encoding="utf-8")

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def save_json(p: Path, data):
    backup(p)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def json_set(obj, path, value, only_if_absent=False, only_if_null=False):
    current = obj
    for key in path[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    last_key = path[-1]
    if only_if_absent and last_key in current:
        return
    if only_if_null and (last_key in current and current[last_key] is not None):
        return
    current[last_key] = value

def ensure_import(py_text: str, module: str, alias=None) -> str:
    pattern = rf"^\s*import\s+{re.escape(module)}\b"
    if re.search(pattern, py_text, re.M):
        return py_text
    import_statement = f"import {module}" if not alias else f"import {module} as {alias}"
    # insert after the first import block or at the top
    lines = py_text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines[:30]):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
            break
    lines.insert(insert_at, import_statement)
    return "\n".join(lines) + ("\n" if not py_text.endswith("\n") else "")

def python_syntax_ok(py_text: str, filename="<string>") -> bool:
    try:
        compile(py_text, filename, "exec")
        return True
    except Exception as e:
        print(f"[GLR] Syntax check failed for {filename}: {e}")
        return False

def op_json_set(file_rel, path, value, only_if_absent=False, only_if_null=False):
    path = TARGET / file_rel
    data = load_json(path)
    json_set(data, path, value, only_if_absent=only_if_absent, only_if_null=only_if_null)
    save_json(path, data)
    # Re-validate
    load_json(path)

def op_ensure_import(file_rel, module, alias=None):
    path = TARGET / file_rel
    text = read_text(path)
    new_text = ensure_import(text, module, alias)
    if new_text != text:
        if not python_syntax_ok(new_text, str(path)):
            return
        write_text(path, new_text)

def op_python_patch(file_rel, pattern, replacement, once=True):
    path = TARGET / file_rel
    text = read_text(path)
    flags = re.M
    count = 1 if once else 0
    new_text = re.sub(pattern, replacement, text, count=count, flags=flags)
    if new_text != text:
        if not python_syntax_ok(new_text, str(path)):
            # try a safer insert if the replacement is multi-line
            pass
        write_text(path, new_text)

def op_python_remove_line_contains(file_rel, contains):
    path = TARGET / file_rel
    text = read_text(path)
    lines = text.splitlines()
    kept_lines = []
    for line in lines:
        if any(c in line and "print(" in line for c in contains):
            continue
        kept_lines.append(line)
    new_text = "\n".join(kept_lines