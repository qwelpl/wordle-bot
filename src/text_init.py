from pathlib import Path

from wordfreq import zipf_frequency


WORDS_FILE = Path("words.txt")
FREQUENCY_FILE = Path("words_frequency.txt")


def load_words() -> list[str]:
    words = []
    for line in WORDS_FILE.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word:
            words.append(word)
    return words


def compute_frequencies(words: list[str]) -> list[tuple[str, float]]:
    data = []
    for word in words:
        freq = zipf_frequency(word, "en")
        data.append((word, freq))
    data.sort(key=lambda item: (-item[1], item[0]))
    return data


def write_frequencies(data: list[tuple[str, float]]) -> None:
    lines = [f"{word} {freq}" for word, freq in data]
    FREQUENCY_FILE.write_text("\n".join(lines), encoding="utf-8")


words = load_words()
frequencies = compute_frequencies(words)
write_frequencies(frequencies)



