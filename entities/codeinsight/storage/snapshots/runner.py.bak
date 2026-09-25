Here's the updated content of the file `runner.py` with the comments and docstrings translated to English while preserving the code behavior and identifiers:

```python
import os, json, logging, shutil, re
from pathlib import Path
from datetime import datetime
from llm_adapter import LLMAdapter
from strategy import CodeInsightStrategy

LOG_FMT = "%(asctime)s ◐ [CodeInsight] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)

def load_json(p):
    """Load JSON data from a file."""
    return json.loads(Path(p).read_text(encoding="utf-8"))

def save_json(p, data):
    """Save JSON data to a file."""
    Path(p).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def snapshot(src: Path, dst_dir: Path):
    """Create a snapshot of a file."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dst_dir / f"{src.name}.{stamp}.bak"
    shutil.copy(src, dst)
    return dst

class Runner:
    def __init__(self, base="."):
        """Initialize the Runner with a base directory."""
        self.base = Path(base)
        self.ghost = load_json(self.base / "ghost.json")
        self.plan = load_json(self.base / "plan.json")
        self.caps = load_json(self.base / "capabilities.json")
        self.mem_path = self.base / self.caps["capability_config"]["state_persistence"]["memory_file"]
        self.memory = json.loads(self.mem_path.read_text(encoding="utf-8")) if self.mem_path.exists() else {"past_reports":[]}

        llm_cfg = self.ghost["LLM_CONFIG"]
        self.llm = LLMAdapter(model=llm_cfg["model"], temperature=llm_cfg.get("temperature",0.4))
        self.seed = (self.base / "seed_prompt.txt").read_text(encoding="utf-8")

        self.snap_dir = self.base / self.caps["capability_config"]["file_snapshots"]["dir"]
        self.reports_dir = self.base / self.caps["capability_config"]["report_generation"]["dir"]
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.strategy = CodeInsightStrategy(self.base, self.llm, self.seed, self.ghost, self.caps, self.memory)

    def run(self):
        """Execute the plan."""
        logging.info("[GL30-O] Starting plan → %s", self.plan["PLAN_NAME"])
        for t in self.plan["TASKS"]:
            logging.info("[GLR] Task: %s — %s", t["id"], t["description"])
            if t["id"] == "audit":
                self.strategy.audit()
            elif t["id"] == "translate_to_english":
                self.strategy.translate_to_english()
            elif t["id"] == "rename_spanish_files":
                self.strategy.rename_spanish_files()
            elif t["id"] == "update_references":
                self.strategy.update_references()
            elif t["id"] == "refactor_pass":
                self.strategy.refactor_pass()
            elif t["id"] == "generate_report":
                self.strategy.generate_report()
        self.memory["timestamp_last_run"] = datetime.now().isoformat()
        save_json(self.mem_path, self.memory)
        logging.info("[GLR] Plan completed.")

if __name__ == "__main__":
    Runner(".").run()
```

This code now has all the comments and strings in English, as per the instructions. The logic and functionality of the code remain unchanged.