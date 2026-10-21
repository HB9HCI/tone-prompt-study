import json
from pathlib import Path

from datasets import load_dataset

DATASET_ID = "cais/mmlu"

subjects = [
    "anatomy",
    "astronomy",
    "college_biology",
    "high_school_us_history",
    "philosophy",
    "professional_law",
]

data_dir = Path("data")
manifest_path = data_dir / "manifest.json"

if not manifest_path.exists():
    raise FileNotFoundError(
        f"Manifest nicht gefunden: {manifest_path}. "
        "Führe zuerst create_manifest.py aus."
    )

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

if manifest["dataset"] != DATASET_ID:
    raise ValueError(
        f"Manifest-Datensatz ist {manifest['dataset']!r}, "
        f"erwartet wurde {DATASET_ID!r}."
    )

rows = []

for subject in subjects:
    dataset = load_dataset(DATASET_ID, subject, split="test")

    expected_fingerprint = manifest["subjects"][subject]["fingerprint"]
    if dataset._fingerprint != expected_fingerprint:
        raise ValueError(
            f"Fingerprint-Abweichung für {subject}: "
            f"Manifest={expected_fingerprint}, "
            f"geladen={dataset._fingerprint}. "
            "Benchmark wurde nicht erstellt."
        )

    if subject == "professional_law":
        original_indices = manifest["law_sampling"]["original_row_indices"]

        if len(original_indices) != 500:
            raise ValueError(
                f"Das Manifest enthält {len(original_indices)} Law-Indizes "
                "statt 500."
            )

        # Die gespeicherten Indizes sind bereits in Auswahlreihenfolge.
        dataset = dataset.select(original_indices)

    for index, item in enumerate(dataset):
        rows.append(
            {
                "subject": subject,
                "item_id": index,
                "question": item["question"],
                "choices": item["choices"],
                "answer": item["answer"],
            }
        )

data_dir.mkdir(exist_ok=True)
output_file = data_dir / "benchmark.jsonl"

with output_file.open("w", encoding="utf-8") as file:
    for row in rows:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Gespeicherte Fragen: {len(rows)}")
print(f"Datei: {output_file}")
