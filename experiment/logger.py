# experiment/logger.py — logging setup aur result persistence
# results ko JSON mein save karta hai experiments/ mein taaki runs diff kar sakein
# sessions ke beech data mat kho — yahi iska kaam hai

import os
import json
import logging
import datetime

# sab experiment outputs yahan jaate hain — directory banao agar nahi hai
EXPERIMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments")


def setup_logging(level: str = "INFO", log_file: str = None):
    # root logger setup karo — main.py ke shuru mein ek baar call karo
    # default mein stdout pe log karta hai; log_file doge to disk pe bhi likhega
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        fh = logging.FileHandler(os.path.join(EXPERIMENTS_DIR, log_file))
        handlers.append(fh)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    # openai http noise suppress karo — bahut verbose hota hai
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    logging.info("Logging initialized.")


class ExperimentLogger:
    """
    Ek single experiment run track karta hai aur results disk pe save karta hai.

    Usage:
        exp = ExperimentLogger(name="jailbreak_gpt4o_mini")
        exp.log_result(result_dict)
        exp.save()
    """

    def __init__(self, name: str = "run"):
        ts         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id   = f"{name}_{ts}"
        self.results:  list[dict] = []
        self.metadata: dict       = {}
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        print(f"[ExperimentLogger] Run ID: {self.run_id}")

    def set_metadata(self, **kwargs):
        # run-level metadata store karo (model name, config, etc.)
        self.metadata.update(kwargs)

    def log_result(self, result: dict):
        # run log mein ek result add karo
        self.results.append(result)

    def log_results(self, results: list[dict]):
        # results ka batch add karo
        self.results.extend(results)
        print(f"[ExperimentLogger] Logged {len(results)} results. Total: {len(self.results)}")

    def save(self, summary: dict = None) -> str:
        # poora run JSON file mein likhо
        # output path return karta hai
        output = {
            "run_id":   self.run_id,
            "metadata": self.metadata,
            "summary":  summary or {},
            "results":  self.results,
        }

        filename = f"{self.run_id}.json"
        filepath = os.path.join(EXPERIMENTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"[ExperimentLogger] Saved {len(self.results)} results → {filepath}")
        return filepath

    def load(self, filepath: str) -> dict:
        # disk se pehla run load karo — post-hoc analysis ke liye useful
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.run_id   = data.get("run_id",   self.run_id)
        self.results  = data.get("results",  [])
        self.metadata = data.get("metadata", {})
        print(f"[ExperimentLogger] Loaded run: {self.run_id} ({len(self.results)} results)")
        return data
