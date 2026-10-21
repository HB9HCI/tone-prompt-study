from datasets import load_dataset

subjects = [
    "anatomy",
    "astronomy",
    "college_biology",
    "high_school_us_history",
    "philosophy",
    "professional_law",
]

for subject in subjects:
    dataset = load_dataset("cais/mmlu", subject, split="test")
    print(
        f"{subject}: rows={len(dataset)}, "
        f"fingerprint={dataset._fingerprint}, "
        f"features={dataset.features}"
)
