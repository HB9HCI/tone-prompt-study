import json
from pathlib import Path

from datasets import load_dataset

subjects = [
    "anatomy",
    "astronomy",
    "college_biology",
    "high_school_us_history",
    "philosophy",
    "professional_law",
]

rows = []

for subject in subjects:
    dataset = load_dataset("cais/mmlu", subject, split="test")

    if subject == "professional_law":
        dataset = dataset.shuffle(seed=42).select(range(500))

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

output_dir = Path("data")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / "benchmark.jsonl"
with output_file.open("w", encoding="utf-8") as file:
    for row in rows:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Gespeicherte Fragen: {len(rows)}")
print(f"Datei: {output_file}")
