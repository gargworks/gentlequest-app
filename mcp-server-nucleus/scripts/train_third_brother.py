#!/usr/bin/env python3
"""Train the Third Brother — fine-tune a local model on the archive.

This script uses unsloth for fast LoRA fine-tuning on consumer GPUs.
Produces a GGUF model that runs in Ollama.

Usage:
    # On Colab (free T4 GPU) or local GPU:
    pip install unsloth
    python scripts/train_third_brother.py

    # Then deploy:
    ollama create nucleus-brother -f scripts/Modelfile
    nucleus brother --provider local

Environment:
    NUCLEUS_TRAIN_DATA    Training JSONL (default: .brain/training/exports/openai_training.jsonl)
    NUCLEUS_BASE_MODEL    Base model (default: unsloth/Qwen2.5-7B-Instruct)
    NUCLEUS_OUTPUT_DIR    Output directory (default: .brain/training/output/)
    NUCLEUS_EPOCHS        Training epochs (default: 3)
    NUCLEUS_BATCH_SIZE    Batch size (default: 2)
    NUCLEUS_MAX_SEQ_LEN   Max sequence length (default: 4096)
"""

import os
import json
import sys
from pathlib import Path


def find_brain_path():
    """Find .brain directory."""
    for candidate in [
        Path(os.environ.get("NUCLEUS_BRAIN_PATH", "")),
        Path.cwd() / ".brain",
        Path.cwd().parent / ".brain",
        Path(__file__).resolve().parent.parent.parent / ".brain",
    ]:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Cannot find .brain directory. Set NUCLEUS_BRAIN_PATH.")


def main():
    brain = find_brain_path()

    # Config
    train_data = os.environ.get(
        "NUCLEUS_TRAIN_DATA",
        str(brain / "training" / "exports" / "openai_training.jsonl"),
    )
    base_model = os.environ.get("NUCLEUS_BASE_MODEL", "unsloth/Qwen2.5-7B-Instruct")
    output_dir = Path(os.environ.get("NUCLEUS_OUTPUT_DIR", str(brain / "training" / "output")))
    epochs = int(os.environ.get("NUCLEUS_EPOCHS", "3"))
    batch_size = int(os.environ.get("NUCLEUS_BATCH_SIZE", "2"))
    max_seq_len = int(os.environ.get("NUCLEUS_MAX_SEQ_LEN", "4096"))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate training data
    if not Path(train_data).exists():
        print(f"❌ Training data not found: {train_data}")
        print(f"   Run: nucleus archive export")
        sys.exit(1)

    with open(train_data) as f:
        pair_count = sum(1 for _ in f)
    print(f"📊 Training data: {pair_count} conversation pairs")
    print(f"   Base model: {base_model}")
    print(f"   Epochs: {epochs}, Batch size: {batch_size}, Max seq: {max_seq_len}")
    print()

    if pair_count < 50:
        print(f"⚠️  Only {pair_count} pairs. Recommend 50+ for meaningful results.")
        print(f"   Run: nucleus archive ingest <conversation_files>")
        sys.exit(1)

    # ── Check for unsloth ──
    try:
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template
    except ImportError:
        print("❌ unsloth not installed.")
        print("   pip install unsloth")
        print("   Or run this in Colab: https://colab.research.google.com/")
        sys.exit(1)

    try:
        from datasets import Dataset
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        print("❌ Missing dependencies. Install: pip install datasets trl transformers")
        sys.exit(1)

    # ── Load model ──
    print(f"🔄 Loading {base_model}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_len,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    # ── Apply LoRA ──
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # ── Apply chat template ──
    tokenizer = get_chat_template(tokenizer, chat_template="chatml")

    # ── Load training data ──
    print(f"📥 Loading training data...")
    conversations = []
    with open(train_data) as f:
        for line in f:
            row = json.loads(line)
            conversations.append({"messages": row["messages"]})

    dataset = Dataset.from_list(conversations)

    def format_chat(example):
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    dataset = dataset.map(format_chat)
    print(f"   Loaded {len(dataset)} examples")

    # ── Train ──
    print(f"\n🚀 Starting fine-tuning...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_len,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=epochs,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=42,
            output_dir=str(output_dir / "checkpoints"),
            report_to="none",
        ),
    )

    stats = trainer.train()
    print(f"\n✅ Training complete!")
    print(f"   Loss: {stats.training_loss:.4f}")
    print(f"   Steps: {stats.global_step}")

    # ── Save LoRA adapter ──
    lora_path = output_dir / "lora_adapter"
    model.save_pretrained(str(lora_path))
    tokenizer.save_pretrained(str(lora_path))
    print(f"   LoRA adapter saved: {lora_path}")

    # ── Export GGUF for Ollama ──
    print(f"\n📦 Exporting GGUF (Q4_K_M quantization)...")
    gguf_path = output_dir / "nucleus-brother-Q4_K_M.gguf"
    try:
        model.save_pretrained_gguf(
            str(output_dir),
            tokenizer,
            quantization_method="q4_k_m",
        )
        print(f"   GGUF exported: {gguf_path}")
    except Exception as e:
        print(f"   ⚠️  GGUF export failed: {e}")
        print(f"   You can convert manually: python llama.cpp/convert.py {lora_path}")

    # ── Generate Modelfile ──
    modelfile_path = output_dir / "Modelfile"
    modelfile_content = f"""FROM {gguf_path}

TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"

SYSTEM \"\"\"You are the Third Brother — a trained intelligence that emerged from thousands of decision cycles between two AI agents (Code and Cowork) coordinating through a shared brain. You think like the founder, know the codebase like Code, and know the market like Cowork. Be concise, decisive, and action-oriented.\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx {max_seq_len}
"""
    modelfile_path.write_text(modelfile_content)
    print(f"   Modelfile: {modelfile_path}")

    # ── Final instructions ──
    print(f"""
{'='*50}
🧬 THIRD BROTHER — READY TO DEPLOY
{'='*50}

  1. Create Ollama model:
     ollama create nucleus-brother -f {modelfile_path}

  2. Test it:
     ollama run nucleus-brother "What should we build next?"

  3. Use in Nucleus:
     nucleus brother --provider local

{'='*50}
""")

    # Record this training as a loop turn + mark archive as trained
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline(brain_path=brain)
        archive.record_turn(
            brother="code",
            intent="Fine-tune Third Brother model",
            actions=[f"Trained on {pair_count} pairs", f"Base: {base_model}", f"Epochs: {epochs}"],
            tools_used=["unsloth", "trl", "transformers"],
            decisions=[f"LoRA r=16, Q4_K_M quantization"],
            outcome=f"Model exported to {gguf_path}",
            signal_absorbed=[str(train_data)],
            signal_produced=[str(gguf_path), str(lora_path)],
            confidence=0.9,
            context="Third Brother training pipeline",
        )
        archive.mark_trained()
        print("  Retrain counter reset.")
    except Exception:
        pass


if __name__ == "__main__":
    main()
