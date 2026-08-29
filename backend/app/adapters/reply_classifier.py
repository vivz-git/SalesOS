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
    "objection",
    "question",
    "positive",
    "not_applicable",
]

Sentiment = Literal["positive", "neutral", "negative"]


class ClassificationResult(BaseModel):
    reply_state: ReplyState
    confidence_score: float
    explanation: str
    needs_human_action: bool
    sentiment: Sentiment = "neutral"


class ReplyClassifierInterface(ABC):
    """Abstract interface for inbound prospect email reply intent classification.

    Isolates intent classification logic so baseline rule engines or future LLM-based
    classifiers can be swapped without touching conversation domain code.
    """

    @abstractmethod
    def classify(self, text_body: str, subject: str = "") -> ClassificationResult:
        """Classify inbound text body and subject into bounded reply taxonomy."""
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
        r"\bnot interested\b",
        r"\bleave me alone\b",
        r"\bplease stop\b",
    ]

    OOO_PATTERNS = [
        r"\bout of (the )?office\b",
        r"\bauto-?reply\b",
        r"\bon vacation\b",
        r"\bautomatic reply\b",
        r"\baway from my desk\b",
        r"\bcurrently away\b",
        r"\bon (maternity|paternity|annual|sick|medical)? ?leave\b",
        r"\breturn(ing)? on\b",
    ]

    REFERRAL_PATTERNS = [
        r"\blooping in\b",
        r"\brefer you to\b",
        r"\bspeak with\b",
        r"\bcontact my colleague\b",
        r"\bcc'?d\b",
        r"\breach out to\b",
        r"\bforwarded to\b",
        r"\btalk to\b",
        r"\bthe right person (is|would be)\b",
    ]

    OBJECTION_PATTERNS = [
        r"\btoo expensive\b",
        r"\balready (using|use|have|work with)\b",
        r"\bcompetitor\b",
        r"\bnot a good fit\b",
        r"\bhappy with our current\b",
        r"\bno need for this\b",
        r"\bcontract with\b",
        r"\bnot looking for\b",
        r"\bdon'?t need\b",
    ]

    NOT_NOW_PATTERNS = [
        r"\bnot right now\b",
        r"\bbad timing\b",
        r"\bcheck back (next|in)\b",
        r"\bnext quarter\b",
        r"\bnot looking right now\b",
        r"\bno budget\b",
        r"\bbusy right now\b",
        r"\bcircl(e|ing) back later\b",
        r"\breach back out in\b",
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
        r"\bbook (a )?time\b",
        r"\bgrab time\b",
        r"\bset up a (call|meeting|chat)\b",
    ]

    QUESTION_PATTERNS = [
        r"\bhow much (does|is|would|do)\b",
        r"\bwhat (is|are) the (pricing|cost|rates|tiers)\b",
        r"\bcan you (explain|share|clarify|provide|send details)\b",
        r"\bhow does (this|it) work\b",
        r"\bdo you integrate with\b",
        r"\bwhat is your pricing\b",
        r"\bcould you tell me\b",
        r"\bquestion about\b",
        r"\bmore information on\b",
        r"\?",
    ]

    def classify(self, text_body: str, subject: str = "") -> ClassificationResult:
        combined_text = f"{subject} {text_body}".lower()

        # 1. Unsubscribe / Opt-Out Check (Highest priority)
        for pat in self.UNSUBSCRIBE_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="unsubscribe",
                    confidence_score=0.95,
                    explanation=f"Matched opt-out pattern '{pat}'",
                    needs_human_action=True,
                    sentiment="negative",
                )

        # 2. Out of Office / Auto-Reply Check
        for pat in self.OOO_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="out_of_office",
                    confidence_score=0.90,
                    explanation=f"Matched out of office pattern '{pat}'",
                    needs_human_action=False,
                    sentiment="neutral",
                )

        # 3. Referral Check
        for pat in self.REFERRAL_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="referral",
                    confidence_score=0.85,
                    explanation=f"Matched referral pattern '{pat}'",
                    needs_human_action=False,
                    sentiment="positive",
                )

        # 4. Objection Check
        for pat in self.OBJECTION_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="objection",
                    confidence_score=0.85,
                    explanation=f"Matched objection pattern '{pat}'",
                    needs_human_action=True,
                    sentiment="negative",
                )

        # 5. Not Now / Timing Objection Check
        for pat in self.NOT_NOW_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="not_now",
                    confidence_score=0.80,
                    explanation=f"Matched bad timing / not now pattern '{pat}'",
                    needs_human_action=False,
                    sentiment="neutral",
                )

        # 6. Interested Check
        for pat in self.INTERESTED_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="interested",
                    confidence_score=0.85,
                    explanation=f"Matched interested / meeting request pattern '{pat}'",
                    needs_human_action=False,
                    sentiment="positive",
                )

        # 7. Question Check
        for pat in self.QUESTION_PATTERNS:
            if re.search(pat, combined_text):
                return ClassificationResult(
                    reply_state="question",
                    confidence_score=0.80,
                    explanation=f"Matched question / inquiry pattern '{pat}'",
                    needs_human_action=True,
                    sentiment="neutral",
                )

        # 8. Ambiguous / Low Confidence Default
        return ClassificationResult(
            reply_state="ambiguous",
            confidence_score=0.40,
            explanation="Unrecognized response pattern requiring human review",
            needs_human_action=True,
            sentiment="neutral",
        )
