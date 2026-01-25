import re
from typing import Iterable

_PUNCT_RE = re.compile(r'[\.,;:!?\-\(\)\[\]\{\}''""`]+ ')

def normalize_text(s: str) -> str:
    """Conservative normalisation used for WER scoring.
    IMPORTANT: apply the SAME normalisation to both GT and hypothesis.
    """
    s = s.strip().lower()
    s = _PUNCT_RE.sub(" ", s)         # remove punctuation (document this choice)
    s = re.sub(r"\s+", " ", s)       # collapse whitespace
    return s.strip()

def normalize_lines(lines: Iterable[str]) -> str:
    """Join lines and normalise as a single reference/hypothesis string."""
    joined = " ".join([ln.strip() for ln in lines if ln.strip()])
    return normalize_text(joined)
