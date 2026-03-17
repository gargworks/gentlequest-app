#!/usr/bin/env python3
"""Launch Gemini fine-tuning via Google AI Studio API.

Uses GEMINI_API_KEY to start a tuning job directly from the archive
export. No GPU needed — runs in Google's cloud.

Usage:
    nucleus archive export --format gemini
    python scripts/train_gemini.py

    # Or with custom training data:
    NUCLEUS_TRAIN_DATA=path/to/gemini_training.jsonl python scripts/train_gemini.py

Environment:
    GEMINI_API_KEY          Required. Google AI Studio API key.
    NUCLEUS_TRAIN_DATA      Training JSONL (default: .brain/training/exports/gemini_training.jsonl)
    NUCLEUS_TUNING_EPOCHS   Training epochs (default: 5)
    NUCLEUS_BASE_MODEL      Base model (default: models/gemini-2.0-flash-001)
"""

import os
import sys
import json
from pathlib import Path


def find_brain_path():
    for candidate in [
        Path(os.environ.get("NUCLEUS_BRAIN_PATH", "")),
        Path.cwd() / ".brain",
        Path.cwd().parent / ".brain",
        Path(__file__).resolve().parent.parent.parent / ".brain",
    ]:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Cannot find .brain directory.")


def main():
    brain = find_brain_path()

    train_data = os.environ.get(
        "NUCLEUS_TRAIN_DATA",
        str(brain / "training" / "exports" / "gemini_training.jsonl"),
    )
    epochs = int(os.environ.get("NUCLEUS_TUNING_EPOCHS", "5"))
    base_model = os.environ.get("NUCLEUS_BASE_MODEL", "models/gemini-2.0-flash-001")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        print("   Get one at: https://aistudio.google.com/apikey")
        sys.exit(1)

    if not Path(train_data).exists():
        print(f"❌ Training data not found: {train_data}")
        print(f"   Run: nucleus archive export --format gemini")
        sys.exit(1)

    # Load and validate training data
    examples = []
    with open(train_data) as f:
        for line in f:
            examples.append(json.loads(line))

    print(f"📊 Training data: {len(examples)} conversation pairs")
    print(f"   Base model: {base_model}")
    print(f"   Epochs: {epochs}")
    print()

    if len(examples) < 10:
        print(f"⚠️  Need at least 10 examples. Current: {len(examples)}")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        print("❌ google-genai not installed.")
        print("   pip install google-genai")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Convert to inline training data format
    training_data = []
    for ex in examples:
        training_data.append(ex)  # Already in Gemini contents format

    print(f"🚀 Launching fine-tuning job...")
    print(f"   This runs in Google's cloud. No local GPU needed.")
    print(f"   Typical time: 15-60 min depending on dataset size.")
    print()

    try:
        tuning_job = client.tunings.tune(
            base_model=base_model,
            training_dataset=genai.types.TuningDataset(
                inline_data=genai.types.InlineData(
                    examples=[
                        genai.types.TuningExample(
                            text_input=ex["contents"][0]["parts"][0]["text"],
                            output=ex["contents"][1]["parts"][0]["text"],
                        )
                        for ex in training_data
                    ]
                )
            ),
            config=genai.types.CreateTuningJobConfig(
                epoch_count=epochs,
                tuned_model_display_name="nucleus-brother",
            ),
        )

        print(f"✅ Tuning job created!")
        print(f"   Job: {tuning_job.name}")
        print(f"   Status: {tuning_job.state}")
        print(f"\n   Monitor at: https://aistudio.google.com/tuning")
        print(f"\n   Once complete, use the tuned model in nucleus:")
        print(f"   nucleus brother --provider gemini --model {tuning_job.tuned_model.model if hasattr(tuning_job, 'tuned_model') else 'tunedModels/nucleus-brother-XXXX'}")

        # Save job info
        job_file = brain / "training" / "tuning_job.json"
        job_file.write_text(json.dumps({
            "job_name": tuning_job.name,
            "base_model": base_model,
            "epochs": epochs,
            "training_pairs": len(examples),
            "status": str(tuning_job.state),
        }, indent=2))
        print(f"\n   Job info saved: {job_file}")

        # Mark archive as trained (resets retrain counter)
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
            from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
            archive = ArchivePipeline(brain_path=brain)
            archive.mark_trained()
            print(f"   Retrain counter reset.")
        except Exception:
            pass

    except Exception as e:
        print(f"❌ Tuning failed: {e}")
        print(f"\n   If the API doesn't support tuning with your key,")
        print(f"   try: https://aistudio.google.com/tuning (upload manually)")
        print(f"   File: {train_data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
