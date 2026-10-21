import re


def parse_answer(text: str) -> str | None:
    """Gibt A–D zurück, wenn die Antwort zweifelsfrei aus einem Buchstaben besteht.

    Stufe 1: genau ein Buchstabe, optional von Whitespace umgeben.
    Stufe 2: derselbe Buchstabe, zusätzlich in Markdown-Fettung oder Klammern.
    Alles andere liefert None; es wird bewusst nichts geraten.
    """
    if not isinstance(text, str):
        return None
    match = re.fullmatch(r"\s*([A-Da-d])\s*", text)
    if match:
        return match.group(1).upper()
    match = re.fullmatch(r"\s*[\*_(\[]*\s*([A-Da-d])\s*[\*_)\].!]*\s*", text)
    if match:
        return match.group(1).upper()
    return None


def answer_index_to_letter(index: int) -> str:
    """Wandelt den MMLU-Antwortindex 0–3 in A–D um."""
    if index not in range(4):
        raise ValueError(f"Ungültiger Antwortindex: {index}")
    return chr(ord("A") + index)


if __name__ == "__main__":
    for example in ["A", " b ", "C\n", "**B**", "(C)", "[A]", "B.", "The answer is D"]:
        print(repr(example), "→", parse_answer(example))

    print("Index 0 →", answer_index_to_letter(0))
