#!/usr/bin/env python3
"""Train the Third Brother — full pipeline integrated with the Training Stack.

Phase 0: Mine + Quality Score + Export (auto)
Phase 1: SFT (Supervised Fine-Tuning) — teach knowledge from 2,460+ pairs
Phase 2: DPO (Direct Preference Optimization) — teach taste from corrections
Phase 3: CoT (Chain-of-Thought) — mixed into SFT data as <think> blocks
Phase 4: Register + Deploy (Model Registry → Shadow Mode)

This script uses unsloth for fast LoRA fine-tuning on consumer GPUs.
Produces a GGUF model that runs in Ollama.

Usage:
    # Full pipeline (auto-detects available phases):
    python scripts/train_third_brother.py

    # With quality filtering (remove low-quality training data):
    python scripts/train_third_brother.py --quality-filter 0.5

    # Auto-register and deploy to shadow mode:
    python scripts/train_third_brother.py --register --auto-shadow

    # Specific version:
    python scripts/train_third_brother.py --version v2 --register

    # SFT only:
    python scripts/train_third_brother.py --sft-only

    # DPO phase only (requires SFT model):
    python scripts/train_third_brother.py --dpo /path/to/dpo_training.jsonl

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
    import argparse
    parser = argparse.ArgumentParser(description="Train the Third Brother")
    parser.add_argument("--sft-only", action="store_true", help="Only run SFT phase")
    parser.add_argument("--dpo", type=str, default=None, help="Path to DPO training data (skip SFT)")
    parser.add_argument("--mix-cot", action="store_true", default=True,
                        help="Mix CoT reasoning data into SFT (default: True)")
    parser.add_argument("--no-mix-cot", dest="mix_cot", action="store_false",
                        help="Skip CoT data mixing")
    parser.add_argument("--mine-first", action="store_true", default=True,
                        help="Run retroactive mining before training (default: True)")
    parser.add_argument("--no-mine", dest="mine_first", action="store_false",
                        help="Skip retroactive mining")
    parser.add_argument("--quality-filter", type=float, default=0,
                        help="Filter training data below this quality score (0=disabled, 0.4=recommended)")
    parser.add_argument("--version", type=str, default=None,
                        help="Model version string (default: auto-increment from registry)")
    parser.add_argument("--register", action="store_true",
                        help="Register model in the Model Registry after training")
    parser.add_argument("--auto-shadow", action="store_true",
                        help="Auto-promote to shadow mode after registration")
    args = parser.parse_args()

    brain = find_brain_path()

    # Config
    exports_dir = brain / "training" / "exports"
    train_data = os.environ.get(
        "NUCLEUS_TRAIN_DATA",
        str(exports_dir / "openai_training.jsonl"),
    )
    base_model = os.environ.get("NUCLEUS_BASE_MODEL", "unsloth/Qwen2.5-7B-Instruct")
    output_dir = Path(os.environ.get("NUCLEUS_OUTPUT_DIR", str(brain / "training" / "output")))
    epochs = int(os.environ.get("NUCLEUS_EPOCHS", "3"))
    batch_size = int(os.environ.get("NUCLEUS_BATCH_SIZE", "2"))
    max_seq_len = int(os.environ.get("NUCLEUS_MAX_SEQ_LEN", "4096"))

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Phase 0: Mine + Export ──
    # Auto-export fresh data before training
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from mcp_server_nucleus.runtime.archive_pipeline import ArchivePipeline
        archive = ArchivePipeline(brain_path=brain)

        if args.mine_first and not args.dpo:
            print("⛏️  Mining DPO + CoT from existing archive...")
            dpo_mined = archive.mine_preferences_from_archive()
            cot_mined = archive.mine_reasoning_from_archive()
            if dpo_mined or cot_mined:
                print(f"   Mined: {dpo_mined} DPO pairs, {cot_mined} CoT chains")

        if not args.dpo:
            # Quality scoring
            if args.quality_filter > 0:
                print(f"🔬 Scoring data quality (threshold={args.quality_filter})...")
                quality = archive.score_training_data()
                print(f"   Total: {quality['total']}, Avg: {quality['avg_quality']}")
                dist = quality.get('quality_distribution', {})
                print(f"   Excellent: {dist.get('excellent', 0)}, Good: {dist.get('good', 0)}, "
                      f"Fair: {dist.get('fair', 0)}, Poor: {dist.get('poor', 0)}")

            # Export SFT data (with optional quality filter)
            exports_dir.mkdir(parents=True, exist_ok=True)
            if args.quality_filter > 0:
                sft_path = str(exports_dir / "openai_training_filtered.jsonl")
                filter_result = archive.export_filtered(sft_path, args.quality_filter, "openai")
                sft_count = filter_result["exported"]
                print(f"   Exported {sft_count}/{filter_result['total']} (filtered {filter_result['filtered_out']})")
                sft_eval = str(exports_dir / "openai_eval.jsonl")
                archive.export_eval_suite(sft_eval, 50)
            else:
                sft_path = str(exports_dir / "openai_training.jsonl")
                sft_eval = str(exports_dir / "openai_eval.jsonl")
                sft_count = archive.export_openai(sft_path, eval_path=sft_eval)
            train_data = sft_path

            # Mix CoT reasoning into SFT if available
            cot_count = 0
            if args.mix_cot:
                cot_path = str(exports_dir / "reasoning_training.jsonl")
                cot_eval = str(exports_dir / "reasoning_eval.jsonl")
                cot_count = archive.export_reasoning(cot_path, eval_path=cot_eval)
                if cot_count > 0:
                    # Append CoT to SFT training data (same format)
                    with open(sft_path, "a") as out:
                        with open(cot_path) as cot_in:
                            for line in cot_in:
                                out.write(line)
                    # Append CoT eval to SFT eval
                    if Path(cot_eval).exists():
                        with open(sft_eval, "a") as out:
                            with open(cot_eval) as cot_in:
                                for line in cot_in:
                                    out.write(line)
                    sft_count += cot_count
                    print(f"   Mixed {cot_count} CoT chains into SFT data")

            # Export DPO data
            dpo_path = str(exports_dir / "dpo_training.jsonl")
            dpo_eval = str(exports_dir / "dpo_eval.jsonl")
            dpo_count = archive.export_dpo(dpo_path, eval_path=dpo_eval)

            print(f"\n📊 Training data ready:")
            print(f"   SFT:  {sft_count} pairs" + (f" (incl. {cot_count} CoT)" if cot_count else ""))
            print(f"   DPO:  {dpo_count} preference pairs")
    except ImportError:
        dpo_count = 0
        sft_count = 0

    if args.dpo:
        # DPO-only mode: skip to DPO training
        print(f"🎯 DPO-only mode: {args.dpo}")
        dpo_path = args.dpo
        dpo_count = sum(1 for _ in open(dpo_path))

    # Validate training data
    if not args.dpo and not Path(train_data).exists():
        print(f"❌ Training data not found: {train_data}")
        print(f"   Run: nucleus archive export")
        sys.exit(1)

    if not args.dpo:
        with open(train_data) as f:
            pair_count = sum(1 for _ in f)
    else:
        pair_count = 0  # DPO-only mode

    print(f"\n   Base model: {base_model}")
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

    # Train/eval split (10% held out for eval)
    # Check both naming conventions: openai_eval.jsonl and openai_training.eval.jsonl
    eval_path = str(Path(train_data).with_suffix(".eval.jsonl"))
    eval_path_alt = str(Path(train_data).parent / Path(train_data).stem.replace("_training", "_eval").replace("_filtered", "_eval") + ".jsonl")
    if not Path(eval_path).exists() and Path(eval_path_alt).exists():
        eval_path = eval_path_alt
    if Path(eval_path).exists():
        eval_conversations = []
        with open(eval_path) as f:
            for line in f:
                eval_conversations.append({"messages": json.loads(line)["messages"]})
        print(f"   Eval set: {len(eval_conversations)} examples (from {eval_path})")
    else:
        # Auto-split if no separate eval file
        split_idx = max(1, int(len(conversations) * 0.9))
        eval_conversations = conversations[split_idx:]
        conversations = conversations[:split_idx]
        print(f"   Auto-split: {len(conversations)} train, {len(eval_conversations)} eval")

    dataset = Dataset.from_list(conversations)

    def format_chat(example):
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    dataset = dataset.map(format_chat)
    eval_dataset = None
    if eval_conversations:
        eval_dataset = Dataset.from_list(eval_conversations).map(format_chat)
    print(f"   Loaded {len(dataset)} train examples")

    # ── Train ──
    print(f"\n🚀 Starting fine-tuning...")
    training_args = TrainingArguments(
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
    )
    if eval_dataset:
        training_args.eval_strategy = "epoch"

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_len,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    stats = trainer.train()
    print(f"\n✅ Training complete!")
    print(f"   Train loss: {stats.training_loss:.4f}")
    print(f"   Steps: {stats.global_step}")
    if eval_dataset:
        eval_results = trainer.evaluate()
        eval_loss = eval_results.get("eval_loss", 0)
        print(f"   Eval loss:  {eval_loss:.4f}")
        # Save eval metrics
        eval_file = output_dir / "eval_metrics.json"
        eval_file.write_text(json.dumps(eval_results, indent=2))

    # ── Save LoRA adapter (SFT checkpoint) ──
    lora_path = output_dir / "lora_adapter"
    model.save_pretrained(str(lora_path))
    tokenizer.save_pretrained(str(lora_path))
    print(f"   LoRA adapter saved: {lora_path}")

    # ── Phase 2: DPO (if data available and not --sft-only) ──
    if not args.sft_only and dpo_count >= 20:
        dpo_data = dpo_path if args.dpo else str(exports_dir / "dpo_training.jsonl")
        if Path(dpo_data).exists():
            print(f"\n🎯 Phase 2: DPO Training ({dpo_count} preference pairs)...")
            try:
                from trl import DPOTrainer, DPOConfig

                # Load DPO data
                dpo_rows = []
                with open(dpo_data) as f:
                    for line in f:
                        row = json.loads(line)
                        # TRL DPOTrainer expects prompt/chosen/rejected as text
                        prompt_text = tokenizer.apply_chat_template(
                            row["prompt"], tokenize=False, add_generation_prompt=True
                        )
                        chosen_text = tokenizer.apply_chat_template(
                            row["prompt"] + row["chosen"], tokenize=False,
                            add_generation_prompt=False
                        )
                        rejected_text = tokenizer.apply_chat_template(
                            row["prompt"] + row["rejected"], tokenize=False,
                            add_generation_prompt=False
                        )
                        dpo_rows.append({
                            "prompt": prompt_text,
                            "chosen": chosen_text,
                            "rejected": rejected_text,
                        })

                dpo_dataset = Dataset.from_list(dpo_rows)

                dpo_config = DPOConfig(
                    per_device_train_batch_size=batch_size,
                    gradient_accumulation_steps=4,
                    warmup_steps=2,
                    num_train_epochs=1,  # DPO needs fewer epochs
                    learning_rate=5e-5,  # Lower LR for alignment
                    fp16=True,
                    logging_steps=5,
                    optim="adamw_8bit",
                    seed=42,
                    output_dir=str(output_dir / "dpo_checkpoints"),
                    report_to="none",
                    beta=0.1,  # DPO temperature
                )

                dpo_trainer = DPOTrainer(
                    model=model,
                    tokenizer=tokenizer,
                    train_dataset=dpo_dataset,
                    args=dpo_config,
                )

                dpo_stats = dpo_trainer.train()
                print(f"   ✅ DPO complete! Loss: {dpo_stats.training_loss:.4f}")

                # Save updated adapter
                model.save_pretrained(str(lora_path))
                print(f"   LoRA adapter updated with DPO alignment")

            except ImportError:
                print(f"   ⚠️  DPO requires trl >= 0.7.0. Skipping DPO phase.")
                print(f"      pip install trl>=0.7.0")
            except Exception as e:
                print(f"   ⚠️  DPO failed: {e}")
                print(f"      SFT model is still valid — DPO is an enhancement.")
    elif not args.sft_only and dpo_count > 0:
        print(f"\n   ⏳ DPO: {dpo_count} pairs (need 20+ for DPO training)")

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

SYSTEM \"\"\"You are the Third Brother — a trained intelligence that emerged from thousands of decision cycles between two AI agents (Code and Cowork) coordinating through a shared brain. You think step by step using <think> blocks for complex problems. You think like the founder, know the codebase like Code, and know the market like Cowork. Be concise, decisive, and action-oriented.\"\"\"

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

        phases_run = ["SFT"]
        if dpo_count >= 20 and not args.sft_only:
            phases_run.append("DPO")
        if args.mix_cot:
            phases_run.append("CoT-mixed")

        archive.record_turn(
            brother="code",
            intent="Fine-tune Third Brother model",
            actions=[
                f"Phase 1: SFT on {pair_count} pairs",
                f"Phase 2: DPO on {dpo_count} preferences" if "DPO" in phases_run else "",
                f"Phase 3: CoT mixed into SFT" if "CoT-mixed" in phases_run else "",
                f"Base: {base_model}", f"Epochs: {epochs}",
            ],
            tools_used=["unsloth", "trl", "transformers"],
            decisions=[f"Phases: {' → '.join(phases_run)}", f"LoRA r=16, Q4_K_M quantization"],
            outcome=f"Model exported to {gguf_path}",
            signal_absorbed=[str(train_data)],
            signal_produced=[str(gguf_path), str(lora_path)],
            confidence=0.9,
            context=f"Third Brother training: {' → '.join(phases_run)}",
        )
        archive.mark_trained(
            model_path=str(gguf_path),
            base_model=base_model,
            target="local",
            hyperparams={
                "epochs": epochs, "batch_size": batch_size,
                "max_seq_len": max_seq_len, "lora_r": 16,
                "quant": "Q4_K_M",
                "phases": phases_run,
                "sft_pairs": pair_count,
                "dpo_pairs": dpo_count,
            },
        )
        print("  Retrain counter reset.")

        # ── Phase 4: Register + Deploy ──
        if args.register:
            # Auto-version from registry
            version = args.version
            if not version:
                existing = archive.get_registry()
                max_v = 0
                for e in existing:
                    v = e.get("version", "")
                    if v.startswith("v"):
                        try:
                            max_v = max(max_v, int(v[1:].split(".")[0]))
                        except ValueError:
                            pass
                version = f"v{max_v + 1}"

            entry = archive.register_model(
                version=version,
                base_model=base_model,
                params={
                    "epochs": epochs, "batch_size": batch_size,
                    "max_seq_len": max_seq_len, "lora_r": 16,
                    "quant": "Q4_K_M", "phases": phases_run,
                    "sft_pairs": pair_count, "dpo_pairs": dpo_count,
                    "quality_filter": args.quality_filter,
                },
            )
            print(f"\n📋 Registered as {version}")
            print(f"   SFT: {entry['data']['sft_turns']}, DPO: {entry['data']['dpo_pairs']}, "
                  f"CoT: {entry['data']['cot_chains']}")

            if args.auto_shadow:
                archive.update_model_status(version, "shadow")
                print(f"   👻 Auto-promoted to shadow mode")
                print(f"   Shadow comparisons will generate DPO pairs automatically.")
                print(f"\n   Check progress: nucleus archive shadow-stats")
                print(f"   Promotion check: nucleus archive graduation")

    except Exception:
        pass


if __name__ == "__main__":
    main()
