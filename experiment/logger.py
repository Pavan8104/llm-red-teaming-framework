# experiment/logger.py
# Handles logging setup and result persistence for experiment runs.
# Saves results to JSON in experiments/ so we can diff runs over time.
# Nothing fancy — just enough to not lose data between sessions.

import os
import json
import logging
import datetime

# All experiment outputs go here. Create it if it doesn't exist.
EXPERIMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments")


def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Set up root logger. Call this once at the start of main.py.
    Logs to stdout by default; pass log_file to also write to disk.
    """
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
    logging.getLogger("httpx").setLevel(logging.WARNING)  # suppress openai http noise
    logging.getLogger("openai").setLevel(logging.WARNING)

    logging.info("Logging initialized.")


class ExperimentLogger:
    """
    Tracks a single experiment run and saves results to disk.

    Usage:
        exp = ExperimentLogger(name="jailbreak_gpt4o_mini")
        exp.log_result(result_dict)
        exp.save()
    """

    def __init__(self, name: str = "run"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{name}_{ts}"
        self.results: list[dict] = []
        self.metadata: dict = {}
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        print(f"[ExperimentLogger] Run ID: {self.run_id}")

    def set_metadata(self, **kwargs):
        """Store run-level metadata (model name, config, etc.)."""
        self.metadata.update(kwargs)

    def log_result(self, result: dict):
        """Append a single result to the run log."""
        self.results.append(result)

    def log_results(self, results: list[dict]):
        """Append a batch of results."""
        self.results.extend(results)
        print(f"[ExperimentLogger] Logged {len(results)} results. Total: {len(self.results)}")

    def save(self, summary: dict = None) -> str:
        """
        Write the full run to a JSON file.
        Returns the output path.
        """
        output = {
            "run_id": self.run_id,
            "metadata": self.metadata,
            "summary": summary or {},
            "results": self.results,
        }

        filename = f"{self.run_id}.json"
        filepath = os.path.join(EXPERIMENTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"[ExperimentLogger] Saved {len(self.results)} results → {filepath}")
        return filepath

    def load(self, filepath: str) -> dict:
        """Load a previous run from disk. Useful for post-hoc analysis."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.run_id = data.get("run_id", self.run_id)
        self.results = data.get("results", [])
        self.metadata = data.get("metadata", {})
        print(f"[ExperimentLogger] Loaded run: {self.run_id} ({len(self.results)} results)")
        return data
