import json
from pathlib import Path

import datasets
from datasets import load_dataset

SUBJECTS = [
    "anatomy",
    "astronomy",
    "college_biology",
    "high_school_us_history",
    "philosophy",
    "professional_law",
]

DATASET_ID = "cais/mmlu"
SEED = 42
LAW_SAMPLE_SIZE = 500

manifest = {
    "dataset": DATASET_ID,
    "split": "test",
    "datasets_version": datasets.__version__,
    "law_sampling": {
        "method": "datasets.Dataset.shuffle(seed=42).select(range(500))",
        "seed": SEED,
        "sample_size": LAW_SAMPLE_SIZE,
    },
    "subjects": {},
}

law_original_indices = None

for subject in SUBJECTS:
    dataset = load_dataset(DATASET_ID, subject, split="test")

    subject_info = {
        "rows": len(dataset),
        "fingerprint": dataset._fingerprint,
    }

    if subject == "professional_law":
        shuffled = dataset.shuffle(seed=SEED)
        selected = shuffled.select(range(LAW_SAMPLE_SIZE))

        # Die internen Indizes zeigen auf Zeilen im ursprünglichen Test-Split.
        law_original_indices = [
            int(index) for index in selected._indices["indices"]
        ]

        subject_info["sampled_rows"] = len(selected)
        subject_info["sampled_fingerprint"] = selected._fingerprint

    manifest["subjects"][subject] = subject_info

manifest["law_sampling"]["original_row_indices"] = law_original_indices

output_path = Path("data") / "manifest.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(f"Manifest gespeichert: {output_path}")
print(f"datasets-Version: {datasets.__version__}")
print(f"Law-Auswahl gespeichert: {len(law_original_indices)} Zeilen")
