import re


def parse_answer(text: str) -> str | None:
    """Gibt A–D zurück, wenn die gesamte Antwort nur ein Buchstabe ist."""
    if not isinstance(text, str):
        return None
    match = re.fullmatch(r"\s*([A-Da-d])\s*", text)
    return match.group(1).upper() if match else None


def answer_index_to_letter(index: int) -> str:
    """Wandelt den MMLU-Antwortindex 0–3 in A–D um."""
    if index not in range(4):
        raise ValueError(f"Ungültiger Antwortindex: {index}")
    return chr(ord("A") + index)


if __name__ == "__main__":
    for example in ["A", " b ", "C\n", "The answer is D"]:
        print(repr(example), "→", parse_answer(example))

    print("Index 0 →", answer_index_to_letter(0))
