import re
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel

ReplyState = Literal[
    "interested",
    "not_now",
    "referral",
    "unsubscribe",
    "out_of_office",
    "ambiguous",
]


class ClassificationResult(BaseModel):
    reply_state: ReplyState
    confidence_score: float
    explanation: str
    needs_human_action: bool


class ReplyClassifierInterface(ABC):
    """Abstract interface for inbound prospect email reply intent classification.

    Isolates intent classification logic so baseline rule engines or future LLM-based
    classifiers can be swapped without touching conversation domain code.
    """

    @abstractmethod
    def classify(self, text_body: str, subject: str = "") -> ClassificationResult:
        """Classify inbound text body and subject into bounded 6-state reply taxonomy."""
        pass


class DeterministicReplyClassifier(ReplyClassifierInterface):
    """Baseline rule-based pattern matching classifier implementing ReplyClassifierInterface."""

    UNSUBSCRIBE_PATTERNS = [
        r"\bunsubscribe\b",
        r"\bremove me\b",
        r"\bstop emailing\b",
        r"\bdo not contact\b",
        r"\bopt out\b",
        r"\btake me off\b",
    ]

    OOO_PATTERNS = [
        r"\bout of (the )?office\b",
        r"\bauto-?reply\b",
        r"\bon vacation\b",
        r"\bautomatic reply\b",
        r"\baway from my desk\b",
        r"\bcurrently away\b",
    ]

    REFERRAL_PATTERNS = [
        r"\blooping in\b",
        r"\brefer you to\b",
        r"\bspeak with\b",
        r"\bcontact my colleague\b",
        r"\bcc'?d\b",
        r"\breach out to\b",
        r"\bforwarded to\b",
    ]

    NOT_NOW_PATTERNS = [
        r"\bnot right now\b",
        r"\bbad timing\b",
        r"\bcheck back (next|in)\b",
        r"\bnext quarter\b",
        r"\bnot looking\b",
        r"\bno budget\b",
        r"\bbusy right now\b",
    ]

    INTERESTED_PATTERNS = [
        r"\bsound(s)? good\b",
        r"\blet'?s (chat|talk|connect|schedule)\b",
        r"\binterested\b",
        r"\bsend (more|over) info\b",
        r"\bopen to\b",
        r"\bfree (on|next|this)\b",
        r"\bcalendar\b",
        r"\bdemo\b",
        r"\bcall\b",
    ]

    def classify(self, text_body: str, subject: str = "") -> ClassificationResult:
        combined_text = f"{subject} {text_body}".lower()

        # 1. Unsubscribe / Opt-Out Check
        for pat in self.UNSUBSCRIBE_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="unsubscribe",
                    confidence_score=0.95,
                    explanation=f"Matched opt-out pattern '{pat}'",
                    needs_human_action=True,
                )

        # 2. Out of Office / Auto-Reply Check
        for pat in self.OOO_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="out_of_office",
                    confidence_score=0.90,
                    explanation=f"Matched out of office pattern '{pat}'",
                    needs_human_action=False,
                )

        # 3. Referral Check
        for pat in self.REFERRAL_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="referral",
                    confidence_score=0.85,
                    explanation=f"Matched referral pattern '{pat}'",
                    needs_human_action=False,
                )

        # 4. Not Now Check
        for pat in self.NOT_NOW_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="not_now",
                    confidence_score=0.80,
                    explanation=f"Matched bad timing / not now pattern '{pat}'",
                    needs_human_action=False,
                )

        # 5. Interested Check
        for pat in self.INTERESTED_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="interested",
                    confidence_score=0.85,
                    explanation=f"Matched interested / meeting request pattern '{pat}'",
                    needs_human_action=False,
                )

        # 6. Ambiguous / Low Confidence Default
        return ClassificationResult(
            reply_state="ambiguous",
            confidence_score=0.40,
            explanation="Unrecognized response pattern requiring human review",
            needs_human_action=True,
        )
