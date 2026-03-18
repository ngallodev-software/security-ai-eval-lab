"""
Quickstart example using FakeReliabilityExecutor (no DB, no API key required).

For the full evaluation run backed by Anthropic + Postgres, use:
    python -m evaluation.runner --dataset datasets/ --name my-run
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.email_threat_agent import EmailThreatInvestigationAgent, FakeReliabilityExecutor


def load_samples(dataset_root: str):
    root = Path(dataset_root)
    for path in sorted(root.rglob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            yield json.load(f)


def main():
    agent = EmailThreatInvestigationAgent(executor=FakeReliabilityExecutor())

    for sample in load_samples("datasets"):
        result = agent.analyze(
            email_text=sample["email_text"],
            sample_id=sample["id"],
        )

        print("=" * 80)
        print(f"sample_id:        {result.sample_id}")
        print(f"actual_label:     {sample['label']}")
        print(f"predicted_label:  {result.predicted_label}")
        print(f"risk_score:       {result.risk_score}")
        print(f"confidence:       {result.confidence}")
        print(f"explanation:      {result.explanation}")
        print(f"signals:          {json.dumps(result.signals, indent=2)}")
        print(f"timeline:         {result.timeline}")


if __name__ == "__main__":
    main()
