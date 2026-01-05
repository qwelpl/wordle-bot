from __future__ import annotations
import argparse
import math
from colorama import Fore
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence, Tuple

try: 
    from wordfreq import zipf_frequency
except ImportError:  
    zipf_frequency = None  
    print("wordfreq library is MISSING!")

word_len = 5
characters = ("b", "y", "g")
char_state = {c: i for i, c in enumerate(characters)}
completion = 3 ** word_len - 1  


def load_words(path: Path) -> List[str]:
    words = []
    for line in path.read_text().splitlines():
        word = line.strip().lower()
        if len(word) == word_len:
            words.append(word)
    if not words:
        raise ValueError(f"No {word_len}-letter words found in {path}")
    return words


def load_frequencies(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    freqs: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        word = parts[0].lower()
        try:
            value = float(parts[1])
        except ValueError:
            continue
        freqs[word] = value
    return freqs


def pattern_code(secret: str, guess: str) -> int:
    states = [0] * word_len
    pool: dict[str, int] = {}
    for idx, (g_char, s_char) in enumerate(zip(guess, secret)):
        if g_char == s_char:
            states[idx] = 2
        else:
            pool[s_char] = pool.get(s_char, 0) + 1
    for idx, g_char in enumerate(guess):
        if states[idx] != 0:
            continue
        remaining = pool.get(g_char, 0)
        if remaining:
            states[idx] = 1
            if remaining == 1:
                del pool[g_char]
            else:
                pool[g_char] = remaining - 1
    value = 0
    for state in states:
        value = value * 3 + state
    return value


def pattern_to_string(code: int) -> str:
    chars = ["b"] * word_len
    for idx in range(word_len - 1, -1, -1):
        state = code % 3
        chars[idx] = characters[state]
        code //= 3
    return "".join(chars)


def string_to_pattern(pattern: str) -> int:
    if len(pattern) != word_len:
        raise ValueError("Pattern must be five characters long")
    value = 0
    for char in pattern.lower():
        if char not in char_state:
            raise ValueError("Pattern may only contain g, y, or b")
        value = value * 3 + char_state[char]
    return value


class WordleSolver:
    def __init__(
        self,
        words: Sequence[str],
        *,
        max_eval_guesses: int = 900,
        full_eval_limit: int = 1500,
        frequencies: Mapping[str, float] | None = None,
    ) -> None:
        self.words = list(words)
        self.max_eval_guesses = max_eval_guesses
        self.full_eval_limit = full_eval_limit
        self._heuristic_ranking = self._rank_words_by_letter_coverage(self.words)
        self._freqs = self._build_frequency_map(self.words, frequencies)

    @staticmethod
    def _build_frequency_map(
        words: Sequence[str], external: Mapping[str, float] | None
    ) -> dict[str, float]:
        freqs: dict[str, float] = {}
        if external:
            for word in words:
                if word in external:
                    freqs[word] = float(external[word])
        if zipf_frequency is not None:
            for word in words:
                freqs.setdefault(word, float(zipf_frequency(word, "en")))
        else:
            for word in words:
                freqs.setdefault(word, 0.0)
        return freqs

    @staticmethod
    def _rank_words_by_letter_coverage(words: Sequence[str]) -> List[str]:
        letter_counts = Counter()
        for word in words:
            letter_counts.update(set(word))

        def score(word: str) -> int:
            used = set()
            total = 0
            for ch in word:
                if ch not in used:
                    total += letter_counts[ch]
                    used.add(ch)
            return total

        return sorted(words, key=score, reverse=True)

    def _top_candidate_words(self, candidates: Sequence[str], cap: int) -> List[str]:
        if len(candidates) <= cap:
            return list(candidates)
        letter_counts = Counter()
        for word in candidates:
            letter_counts.update(set(word))

        def score(word: str) -> int:
            seen = set()
            total = 0
            for ch in word:
                if ch not in seen:
                    total += letter_counts[ch]
                    seen.add(ch)
            return total

        ranked = sorted(candidates, key=score, reverse=True)
        return ranked[:cap]

    def guess_space(self, candidates: Sequence[str]) -> Sequence[str]:
        if len(candidates) <= self.full_eval_limit:
            return self.words
        subset = self._top_candidate_words(candidates, self.max_eval_guesses // 2)
        seen = set(subset)
        for word in self._heuristic_ranking:
            if len(subset) >= self.max_eval_guesses:
                break
            if word in seen:
                continue
            subset.append(word)
            seen.add(word)
        return subset

    def expected_information(self, guess: str, candidates: Sequence[str]) -> float:
        counts: defaultdict[int, int] = defaultdict(int)
        for answer in candidates:
            counts[pattern_code(answer, guess)] += 1
        total = len(candidates)
        frequency = 0.0
        for count in counts.values():
            p = count / total
            frequency -= p * math.log2(p)
        return frequency

    def best_guess(self, candidates: Sequence[str]) -> Tuple[str, float]:
        guess_pool = self.guess_space(candidates)
        candidate_set = set(candidates)
        best_word = None
        best_key: Tuple[float, bool, float] | None = None
        for guess in guess_pool:
            frequency = self.expected_information(guess, candidates)
            metadata = (frequency, guess in candidate_set, self._freqs.get(guess, 0.0))
            if best_key is None or metadata > best_key:
                best_key = metadata
                best_word = guess
        if best_word is None:
            raise RuntimeError("Failed to select a guess")
        return best_word, best_key[0]

    def filter_candidates(
        self, candidates: Sequence[str], guess: str, feedback_code: int
    ) -> List[str]:
        return [word for word in candidates if pattern_code(word, guess) == feedback_code]


def autoplay(solver: WordleSolver, answer: str, max_steps: int) -> None:
    answer = answer.lower()
    if len(answer) != word_len:
        raise ValueError("Answer must be a five-letter word")
    candidates = solver.words[:]
    for attempt in range(1, max_steps + 1):
        guess, frequency = solver.best_guess(candidates)
        feedback = pattern_code(answer, guess)
        pattern_str = pattern_to_string(feedback)
        remaining = len(candidates)
        print(
            f"Guess {attempt}: {guess.upper()} | frequency={frequency:.3f} | "
            f"search space={remaining} | feedback={pattern_str}"
        )
        candidates = solver.filter_candidates(candidates, guess, feedback)
    print("Failed to crack the word within the allotted steps.")


def interactive_session(solver: WordleSolver, max_steps: int) -> None:
    print("Enter feedback as a string of five letters (" + Fore.GREEN + "g=green," + Fore.YELLOW + "y=yellow," + Fore.WHITE + "b=gray).")
    candidates = solver.words[:]
    for attempt in range(1, max_steps + 1):
        guess, frequency = solver.best_guess(candidates)
        print(
            f"Guess {attempt}: {guess.upper()} | frequency={frequency:.3f} | "
            f"remaining={len(candidates)}"
        )
        pattern = input("Feedback? ").strip().lower()
        try:
            code = string_to_pattern(pattern)
        except ValueError as exc:  # pragma: no cover - user input validation
            print(f"Invalid pattern: {exc}")
            return
        if code == completion:
            print("Congratulations! Word identified.")
            return
        candidates = solver.filter_candidates(candidates, guess, code)
        if not candidates:
            print("No candidates left. Did the feedback contain a mistake?")
            return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Information-theoretic Wordle solver")
    parser.add_argument(
        "--words",
        type=Path,
        default=Path("files/words.txt"),
        help="Path to list of allowed words (default: files/words.txt)",
    )
    parser.add_argument(
        "--answer",
        type=str,
        help="Simulate a full solve against the provided answer",
    )
    parser.add_argument(
        "--frequencies",
        type=Path,
        default=Path("files/words_frequency.txt"),
        help="Optional path to a cached 'word frequency' table for tie-breaking",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="Maximum number of guesses to perform (default: 6)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    words = load_words(args.words)
    freq_table = load_frequencies(args.frequencies)
    solver = WordleSolver(words, frequencies=freq_table)
    if args.answer:
        autoplay(solver, args.answer, args.max_steps)
    else:
        interactive_session(solver, args.max_steps)


if __name__ == "__main__":
    main()
