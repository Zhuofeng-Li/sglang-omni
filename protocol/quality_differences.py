"""Export changed normalized transcripts and WER direction across paired repetitions."""
import json
import os
from pathlib import Path

ROOT = Path(os.environ["QUAL_ROOT"])
comparisons = []
for pr in [2880, 2881, 2882]:
    for concurrency in [1, 16, 32, 64]:
        for mode in ["nonstream", "stream"]:
            pairs = [(42, ""), (43, "")]
            if concurrency == 32:
                pairs += [(42, "-fixed-seed42-repeat1"), (42, "-fixed-seed42-repeat2")]
            for seed, suffix in pairs:
                for language in ["en", "zh"]:
                    stem = f"pr{pr}-c{concurrency}-{mode}"
                    main_path = ROOT / "results" / f"{stem}-main-seed{seed}{suffix}" / f"{language}-raw.json"
                    pr_path = ROOT / "results" / f"{stem}-pr-seed{seed}{suffix}" / f"{language}-raw.json"
                    assert main_path.exists() and pr_path.exists(), (str(main_path), str(pr_path))
                    left = json.loads(main_path.read_text())
                    right = json.loads(pr_path.read_text())
                    before = {row["id"]: row for row in left["per_sample"]}
                    after = {row["id"]: row for row in right["per_sample"]}
                    assert before.keys() == after.keys()
                    changes = []
                    for sample_id, baseline in before.items():
                        candidate = after[sample_id]
                        assert baseline["ref_norm"] == candidate["ref_norm"]
                        if baseline["hyp_norm"] != candidate["hyp_norm"]:
                            changes.append({"id": sample_id, "reference": baseline["ref_norm"], "main": baseline["hyp_norm"], "pr": candidate["hyp_norm"], "main_wer": baseline["wer"], "pr_wer": candidate["wer"], "main_success": baseline["is_success"], "pr_success": candidate["is_success"]})
                    comparisons.append({"pr": pr, "concurrency": concurrency, "mode": mode, "seed": seed, "repetition": suffix or "original", "attempted": len(before), "language": language, "normalized_transcripts_changed": len(changes), "corpus_wer_main": left["summary"]["corpus_wer"], "corpus_wer_pr": right["summary"]["corpus_wer"], "changes": changes})
output = ROOT / "control/quality-differences.json"
temporary = output.with_suffix(".partial")
temporary.write_text(json.dumps({"comparisons": comparisons}, ensure_ascii=False, indent=2))
temporary.replace(output)
