"""SalesOS evaluation harness.

Produces reproducible, honest evidence for three of the four "Results" metrics
published in the repository README:

  1. Reply-intent classification accuracy (DeterministicReplyClassifier)
  2. Human-approval outcome distribution for AI-generated outreach drafts
  3. Automated test counts (backend + frontend) and backend coverage

The fourth metric (estimated human-effort savings) is not measured here — it is
an explicitly labeled assumption-based estimate, documented directly in the
README and in `time_savings_estimate()` below.

Design notes
------------
* Part 1 runs the ACTUAL classifier code (`app.adapters.reply_classifier
  .DeterministicReplyClassifier`) against a synthetic labeled dataset. No
  network calls, no LLM, fully deterministic.
* Part 2 exercises the ACTUAL FastAPI draft lifecycle (create -> generate ->
  revise -> submit-review -> approve/reject) against an in-memory SQLite
  database, using the same kind of deterministic, no-network LLM provider
  mock already used by the project's own test suite
  (backend/tests/test_e2e_workflow.py::MockLLMProvider). No real email
  provider is wired up and `/v1/deliveries` is never called, so no outbound
  email can be sent by this script.
* The "approved as-is / approved with edits / rejected" decision is produced
  by a small, fully deterministic scoring rubric (`score_draft`) applied to
  the generated draft content. This rubric is a synthetic stand-in for a
  human reviewer for the purposes of this evaluation only — it does not
  represent and is not claimed to represent real human judgment, and the
  README must not describe it as such.
* Part 3 shells out to the project's own configured test runners
  (`pytest --cov=app`, `vitest run`) rather than reimplementing test
  collection, so the numbers always match what a reviewer gets by running
  those commands directly. Results are parsed from each tool's structured
  file report (JUnit XML / coverage JSON / vitest JSON), not scraped from
  terminal output, which was observed to be unreliable for large runs in
  this environment.

Run with:
    cd backend
    python -m evaluation.evaluate_salesos
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


# ---------------------------------------------------------------------------
# Part 1: Reply-intent classification accuracy
# ---------------------------------------------------------------------------


def run_reply_intent_eval() -> dict[str, Any]:
    from app.adapters.reply_classifier import DeterministicReplyClassifier

    dataset = json.loads((DATASETS_DIR / "reply_intent_cases.json").read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = dataset["cases"]
    labels: list[str] = dataset["label_set"]

    classifier = DeterministicReplyClassifier()

    per_case: list[dict[str, Any]] = []
    correct = 0
    confusion: dict[str, Counter[str]] = {lbl: Counter() for lbl in labels}

    for case in cases:
        result = classifier.classify(case["body"], case.get("subject", ""))
        predicted = result.reply_state
        true_label = case["true_label"]
        is_correct = predicted == true_label
        if is_correct:
            correct += 1
        confusion[true_label][predicted] += 1
        per_case.append(
            {
                "id": case["id"],
                "true_label": true_label,
                "predicted_label": predicted,
                "correct": is_correct,
                "confidence_score": result.confidence_score,
            }
        )

    total = len(cases)
    incorrect = total - correct
    accuracy = correct / total if total else 0.0

    per_class: dict[str, dict[str, Any]] = {}
    for lbl in labels:
        tp = confusion[lbl][lbl]
        support = sum(confusion[lbl].values())
        predicted_as_lbl = sum(confusion[other][lbl] for other in labels)
        precision = tp / predicted_as_lbl if predicted_as_lbl else None
        recall = tp / support if support else None
        per_class[lbl] = {
            "support": support,
            "predicted_count": predicted_as_lbl,
            "true_positive": tp,
            "precision": round(precision, 4) if precision is not None else None,
            "recall": round(recall, 4) if recall is not None else None,
        }

    confusion_matrix = {true_lbl: dict(confusion[true_lbl]) for true_lbl in labels}

    return {
        "dataset_size": total,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(accuracy, 4),
        "label_set": labels,
        "per_class_metrics": per_class,
        "confusion_matrix": confusion_matrix,
        "cases": per_case,
        "method": (
            "app.adapters.reply_classifier.DeterministicReplyClassifier.classify() run directly "
            "against evaluation/datasets/reply_intent_cases.json (synthetic, hand-labeled). "
            "No LLM or external API involved; fully deterministic and reproducible."
        ),
    }


# ---------------------------------------------------------------------------
# Part 2: Human approval outcome distribution
# ---------------------------------------------------------------------------

GENERIC_SUBJECT_FRAGMENT = "Accelerating Your Core Platform"
GENERIC_ROLE_FRAGMENT = "Given your role as leader"
GENERIC_SEGMENT_FRAGMENT = "focusing on engineering"


def score_draft(subject: str, body: str, evidence_references: list[dict[str, Any]]) -> tuple[int, dict[str, bool]]:
    """Deterministic synthetic review rubric.

    Scores a generated draft 0-4 on observable personalization signals. This
    is NOT the production human reviewer and does not claim to predict what a
    human would decide -- it is a fixed, inspectable stand-in used only to
    produce a reproducible outcome label for this evaluation.
    """
    checks = {
        "named_account": GENERIC_SUBJECT_FRAGMENT not in subject,
        "role_specific": GENERIC_ROLE_FRAGMENT not in body,
        "segment_specific": GENERIC_SEGMENT_FRAGMENT not in body,
        "evidence_grounded": len(evidence_references) > 0,
    }
    return sum(checks.values()), checks


def outcome_for_score(score: int) -> str:
    if score == 4:
        return "approved_as_is"
    if score in (2, 3):
        return "approved_with_edits"
    return "rejected"


async def _run_approval_eval_async() -> dict[str, Any]:
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import event
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.pool import StaticPool

    from app.adapters.llm_provider import (
        LLMGenerationRequest,
        LLMGenerationResult,
        LLMProviderInterface,
        ResearchSynthesisRequest,
        ResearchSynthesisResult,
    )
    from app.api.outreach import get_llm_provider
    from app.auth import AuthUser, Principal, get_current_principal, get_current_user
    from app.core.config import Settings, get_settings
    from app.db import get_db_session
    from app.main import app
    from app.models import Base

    @compiles(JSONB, "sqlite")
    def _compile_jsonb_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
        return "JSON"

    @compiles(PGUUID, "sqlite")
    def _compile_pguuid_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
        return "CHAR(36)"

    class EvalDeterministicLLMProvider(LLMProviderInterface):
        """Deterministic, no-network draft generator for this evaluation.

        Mirrors the pattern already used by the project's own test suite
        (tests/test_e2e_workflow.py::MockLLMProvider) so that running this
        evaluation never spends LLM API credits or depends on network access.
        """

        def generate_outreach_draft(self, request: LLMGenerationRequest) -> LLMGenerationResult:
            evidence = []
            for s in request.research_sources[:2]:
                evidence.append(
                    {
                        "url": s.get("url"),
                        "title": s.get("title"),
                        "snippet": s.get("snippet"),
                        "source_type": s.get("source_type", "website"),
                    }
                )
            return LLMGenerationResult(
                subject=f"Accelerating {request.account_name or 'Your'} Core Platform",
                body=(
                    f"Hi {request.contact_name},\n\n"
                    f"I noticed {request.account_name or 'your team'} is actively "
                    f"{request.target_segment or 'focusing on engineering'}. "
                    f"Given your role as {request.contact_title or 'leader'}, our solution helps "
                    f"streamline outbound sales with governed human-in-the-loop workflows.\n\n"
                    f"Best regards,\nSalesOS Team"
                ),
                generation_source="ai_generated",
                provider="eval-deterministic-mock",
                model="eval-deterministic-mock-v1",
                prompt_version=request.prompt_version,
                evidence_references=evidence,
                token_usage=None,
                estimated_cost=0.0,
                duration_ms=1,
            )

        def generate_research_synthesis(self, request: ResearchSynthesisRequest) -> ResearchSynthesisResult:
            raise NotImplementedError("not exercised by this evaluation")

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_conn: Any, _: Any) -> None:
        dbapi_conn.create_function("set_config", 3, lambda name, val, is_local: val)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

    workspace_id = uuid4()
    user_id = uuid4()
    principal = Principal(user_id=user_id, email="evaluator@salesos-eval.dev", workspace_id=workspace_id, role="owner")
    auth_user = AuthUser(user_id=user_id, email="evaluator@salesos-eval.dev")
    mock_llm = EvalDeterministicLLMProvider()
    settings = Settings(environment="test", resend_from_email="eval@salesos-eval.dev", frontend_url="https://eval.salesos.dev")

    async def _override_db() -> Any:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_principal] = lambda: principal
    app.dependency_overrides[get_current_user] = lambda: auth_user
    app.dependency_overrides[get_llm_provider] = lambda: mock_llm
    app.dependency_overrides[get_settings] = lambda: settings

    headers = {"X-SalesOS-Workspace-Id": str(workspace_id), "Authorization": "Bearer eval_mock_token"}

    prospects = json.loads((DATASETS_DIR / "approval_prospects.json").read_text(encoding="utf-8"))["prospects"]
    records: list[dict[str, Any]] = []

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://eval") as client:
            for p in prospects:
                account_id: str | None = None
                if p["account_name"]:
                    acc_resp = await client.post(
                        "/v1/accounts",
                        json={"name": p["account_name"], "domain": p["domain"], "industry": p["industry"]},
                        headers=headers,
                    )
                    assert acc_resp.status_code == 201, acc_resp.text
                    account_id = acc_resp.json()["id"]

                campaign_id: str | None = None
                if p["campaign_segment"]:
                    camp_resp = await client.post(
                        "/v1/campaigns",
                        json={"name": f"Eval Campaign {p['id']}", "target_segment": p["campaign_segment"]},
                        headers=headers,
                    )
                    assert camp_resp.status_code == 201, camp_resp.text
                    campaign_id = camp_resp.json()["id"]

                contact_payload: dict[str, Any] = {
                    "first_name": p["contact_first"],
                    "last_name": p["contact_last"],
                    "email": f"{p['contact_first'].lower()}.{p['contact_last'].lower()}@{(p['domain'] or 'example.test')}",
                }
                if account_id:
                    contact_payload["account_id"] = account_id
                if p["title"]:
                    contact_payload["title"] = p["title"]
                if p["department"]:
                    contact_payload["department"] = p["department"]
                contact_resp = await client.post("/v1/contacts", json=contact_payload, headers=headers)
                assert contact_resp.status_code == 201, contact_resp.text
                contact_id = contact_resp.json()["id"]

                research_brief_id: str | None = None
                if p["research"] and account_id:
                    brief_resp = await client.post(
                        "/v1/research/briefs",
                        json={
                            "account_id": account_id,
                            "contact_id": contact_id,
                            "summary": f"{p['account_name']} is expanding its {p['industry']} initiatives.",
                            "key_findings": [
                                f"{p['account_name']} recently announced growth in {p['industry']}.",
                                "Actively hiring for revenue and operations roles.",
                            ],
                        },
                        headers=headers,
                    )
                    assert brief_resp.status_code == 201, brief_resp.text
                    research_brief_id = brief_resp.json()["id"]
                    for src in (
                        {"url": f"https://{p['domain']}/news/growth", "title": f"{p['account_name']} Growth Update", "snippet": "Company announces expansion.", "confidence": 0.9},
                        {"url": f"https://{p['domain']}/careers", "title": f"Careers at {p['account_name']}", "snippet": "Hiring across revenue and operations.", "confidence": 0.85},
                    ):
                        src_resp = await client.post(
                            f"/v1/research/briefs/{research_brief_id}/sources", json=src, headers=headers
                        )
                        assert src_resp.status_code == 201, src_resp.text

                draft_payload: dict[str, Any] = {
                    "contact_id": contact_id,
                    "subject": "Initial Scaffold Subject",
                    "body": "Initial Scaffold Body",
                    "generation_source": "human",
                }
                if campaign_id:
                    draft_payload["campaign_id"] = campaign_id
                if research_brief_id:
                    draft_payload["research_brief_id"] = research_brief_id
                draft_resp = await client.post("/v1/outreach/drafts", json=draft_payload, headers=headers)
                assert draft_resp.status_code == 201, draft_resp.text
                draft_id = draft_resp.json()["id"]

                gen_resp = await client.post(f"/v1/outreach/drafts/{draft_id}/actions/generate", headers=headers)
                assert gen_resp.status_code == 200, gen_resp.text
                generated = gen_resp.json()
                ai_version_number = generated["current_version_number"]

                versions_resp = await client.get(f"/v1/outreach/drafts/{draft_id}/versions", headers=headers)
                assert versions_resp.status_code == 200
                ai_version = next(v for v in versions_resp.json() if v["version_number"] == ai_version_number)
                evidence_references = ai_version.get("evidence_references") or []

                score, checks = score_draft(generated["current_subject"], generated["current_body"], evidence_references)
                outcome = outcome_for_score(score)

                final_version_number = ai_version_number
                if outcome == "approved_with_edits":
                    revise_resp = await client.post(
                        f"/v1/outreach/drafts/{draft_id}/actions/revise",
                        json={
                            "subject": generated["current_subject"],
                            "body": generated["current_body"]
                            + "\n\n[Reviewer edit: added manual personalization and context before sending.]",
                            "generation_source": "ai_assisted",
                        },
                        headers=headers,
                    )
                    assert revise_resp.status_code == 200, revise_resp.text
                    final_version_number = revise_resp.json()["current_version_number"]

                submit_resp = await client.post(f"/v1/outreach/drafts/{draft_id}/actions/submit-review", headers=headers)
                assert submit_resp.status_code == 200, submit_resp.text

                if outcome == "rejected":
                    decision_resp = await client.post(
                        f"/v1/approvals/{draft_id}/actions/reject",
                        json={"notes": "Synthetic rubric: insufficient personalization/evidence grounding."},
                        headers=headers,
                    )
                else:
                    decision_resp = await client.post(
                        f"/v1/approvals/{draft_id}/actions/approve",
                        json={"notes": f"Synthetic rubric outcome: {outcome} (score {score}/4)."},
                        headers=headers,
                    )
                assert decision_resp.status_code == 200, decision_resp.text

                records.append(
                    {
                        "prospect_id": p["id"],
                        "tier": p["tier"],
                        "account_name": p["account_name"],
                        "rubric_score": score,
                        "rubric_checks": checks,
                        "outcome": outcome,
                        "ai_generated_version": ai_version_number,
                        "final_version": final_version_number,
                        "final_draft_status": decision_resp.json()["decision"] if "decision" in decision_resp.json() else None,
                    }
                )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

    total = len(records)
    counts = Counter(r["outcome"] for r in records)
    approved_as_is = counts.get("approved_as_is", 0)
    approved_with_edits = counts.get("approved_with_edits", 0)
    rejected = counts.get("rejected", 0)

    return {
        "dataset_size": total,
        "approved_as_is": approved_as_is,
        "approved_with_edits": approved_with_edits,
        "rejected": rejected,
        "approved_as_is_pct": round(100 * approved_as_is / total, 1) if total else 0.0,
        "approved_with_edits_pct": round(100 * approved_with_edits / total, 1) if total else 0.0,
        "rejected_pct": round(100 * rejected / total, 1) if total else 0.0,
        "records": records,
        "rubric": {
            "checks": ["named_account", "role_specific", "segment_specific", "evidence_grounded"],
            "outcome_thresholds": {"approved_as_is": "score == 4", "approved_with_edits": "score in {2,3}", "rejected": "score in {0,1}"},
        },
        "method": (
            "Real FastAPI draft lifecycle (create -> generate -> [revise] -> submit-review -> approve/reject) "
            "run against an in-memory SQLite database via httpx ASGITransport, using a deterministic no-network "
            "LLM provider mock (same pattern as tests/test_e2e_workflow.py). Outcome per draft is assigned by a "
            "fixed, deterministic scoring rubric (score_draft) applied to the generated content -- a synthetic "
            "stand-in for human review, not a measurement of real human judgment. No outbound email is sent; "
            "/v1/deliveries is never called."
        ),
        "caveat": (
            "This distribution shows what the synthetic rubric decided for this synthetic dataset. It does not "
            "demonstrate that SalesOS's human approval step 'catches bad drafts' in production -- it demonstrates "
            "that the draft generation and approval lifecycle behaves correctly end-to-end, and that draft quality "
            "(and therefore this rubric's outcome) tracks how complete the input research/context is."
        ),
    }


def run_approval_eval() -> dict[str, Any]:
    return asyncio.run(_run_approval_eval_async())


# ---------------------------------------------------------------------------
# Part 3: Test / coverage evidence
# ---------------------------------------------------------------------------


def run_backend_tests_with_coverage() -> dict[str, Any]:
    """Run the backend suite and parse results from file-based reports.

    Note: in this environment, pytest's final stdout summary line is
    occasionally dropped by the subprocess output capture layer on large
    runs (observed directly while building this script). Parsing that line
    with a regex is therefore unreliable. `--junitxml` and `--cov-report=json`
    write structured results straight to disk, sidestepping the issue
    entirely and giving results that don't depend on stdout capture at all.
    """
    import xml.etree.ElementTree as ET

    coverage_json_path = RESULTS_DIR / "_backend_coverage.json"
    junit_xml_path = RESULTS_DIR / "_backend_junit.xml"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--cov=app",
        "--cov-report=term-missing",
        f"--cov-report=json:{coverage_json_path}",
        f"--junitxml={junit_xml_path}",
    ]
    proc = subprocess.run(cmd, cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=600)

    passed = failed = errors = skipped = total = 0
    if junit_xml_path.exists():
        root = ET.parse(junit_xml_path).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        attrib = suite.attrib if suite is not None else {}
        total = int(attrib.get("tests", 0))
        failed = int(attrib.get("failures", 0))
        errors = int(attrib.get("errors", 0))
        skipped = int(attrib.get("skipped", 0))
        passed = total - failed - errors - skipped

    coverage_pct = None
    if coverage_json_path.exists():
        cov_data = json.loads(coverage_json_path.read_text(encoding="utf-8"))
        coverage_pct = round(cov_data.get("totals", {}).get("percent_covered", 0.0), 2)

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "total": total,
        "exit_code": proc.returncode,
        "coverage_percent": coverage_pct,
        "coverage_source": "pytest-cov (already configured in backend/pyproject.toml addopts)",
        "method": (
            "pytest -q --cov=app --cov-report=term-missing --cov-report=json --junitxml=... "
            "(run from backend/); counts parsed from the JUnit XML and coverage JSON reports, "
            "not from stdout."
        ),
    }


def run_frontend_tests() -> dict[str, Any]:
    """Run the frontend suite and parse results from vitest's JSON reporter.

    Invoking `pnpm test -- --reporter=json` does not work here: pnpm forwards
    the literal `--` token to vitest's CLI, which then treats everything
    after it as positional arguments rather than flags (verified while
    building this script), so the JSON reporter never activates. Calling the
    vitest binary directly with `--reporter=json --outputFile=...` avoids
    that and writes a structured result file we can parse without relying on
    terminal output.
    """
    frontend_dir = REPO_ROOT / "frontend"
    vitest_bin = frontend_dir / "node_modules" / ".bin" / ("vitest.CMD" if sys.platform == "win32" else "vitest")
    results_path = RESULTS_DIR / "_frontend_vitest.json"

    if not vitest_bin.exists():
        return {
            "passed": None,
            "total": None,
            "exit_code": None,
            "coverage_percent": None,
            "coverage_available": False,
            "note": f"vitest binary not found at {vitest_bin}; run `pnpm test` manually in frontend/.",
        }

    cmd = [str(vitest_bin), "run", "--reporter=json", f"--outputFile={results_path}"]
    proc = subprocess.run(cmd, cwd=str(frontend_dir), capture_output=True, text=True, timeout=600)

    total = passed = failed = suites = None
    if results_path.exists():
        data = json.loads(results_path.read_text(encoding="utf-8"))
        total = data.get("numTotalTests")
        passed = data.get("numPassedTests")
        failed = data.get("numFailedTests")
        suites = data.get("numTotalTestSuites")

    test_file_count = len(list((frontend_dir / "src").rglob("*.test.ts*")))

    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "test_suite_count": suites,
        "test_file_count": test_file_count,
        "exit_code": proc.returncode,
        "coverage_percent": None,
        "coverage_available": False,
        "coverage_note": (
            "No coverage provider (e.g. @vitest/coverage-v8) is installed or configured in "
            "frontend/vitest.config.ts or package.json/pnpm-lock.yaml. Introducing one was out of scope for "
            "this evaluation, so frontend results report test counts only, not a coverage percentage."
        ),
        "method": (
            "node_modules/.bin/vitest run --reporter=json --outputFile=... from frontend/; "
            "counts parsed from vitest's JSON report, not from stdout."
        ),
    }


# ---------------------------------------------------------------------------
# Part 4: Estimated time savings (explicitly an estimate, not a measurement)
# ---------------------------------------------------------------------------


def time_savings_estimate() -> dict[str, Any]:
    return {
        "type": "ESTIMATE",
        "manual_minutes_range": [15, 20],
        "manual_description": "Manually researching a prospect and drafting personalized outreach by hand.",
        "salesos_minutes_range": [2, 3],
        "salesos_description": "Human review/edit/approval time per AI-generated draft in SalesOS's approval queue.",
        "note": (
            "These are assumption-based reference points, not a measured benchmark from a timed user study. "
            "No percentage or multiplier claim is derived from them; the README presents the two ranges side by side."
        ),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] Running reply-intent classification evaluation...")
    reply_intent = run_reply_intent_eval()
    print(f"      accuracy={reply_intent['accuracy']:.4f} ({reply_intent['correct']}/{reply_intent['dataset_size']})")

    print("[2/4] Running human approval outcome evaluation...")
    approval = run_approval_eval()
    print(
        f"      as_is={approval['approved_as_is']} with_edits={approval['approved_with_edits']} "
        f"rejected={approval['rejected']} (n={approval['dataset_size']})"
    )

    print("[3/4] Running backend tests with coverage (pytest --cov)...")
    backend_tests = run_backend_tests_with_coverage()
    print(f"      backend: {backend_tests['passed']} passed, coverage={backend_tests['coverage_percent']}%")

    print("[3/4] Running frontend tests (pnpm test)...")
    frontend_tests = run_frontend_tests()
    print(f"      frontend: {frontend_tests['passed']} passed of {frontend_tests['total']}")

    print("[4/4] Recording time-savings estimate (not measured)...")
    time_savings = time_savings_estimate()

    results = {
        "schema_version": 1,
        "reply_intent_classification": reply_intent,
        "approval_outcomes": approval,
        "tests_and_coverage": {
            "backend": backend_tests,
            "frontend": frontend_tests,
        },
        "estimated_time_savings": time_savings,
    }

    out_path = RESULTS_DIR / "salesos-results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {out_path}")

    write_markdown_report(results)


def write_markdown_report(results: dict[str, Any]) -> None:
    ri = results["reply_intent_classification"]
    ap = results["approval_outcomes"]
    bt = results["tests_and_coverage"]["backend"]
    ft = results["tests_and_coverage"]["frontend"]
    ts = results["estimated_time_savings"]

    lines = [
        "# SalesOS Evaluation Report",
        "",
        "Generated by `backend/evaluation/evaluate_salesos.py`. All classification and approval numbers below are",
        "measured by running the application's real code paths against synthetic datasets checked into",
        "`backend/evaluation/datasets/`. See that script's module docstring for exact methodology and caveats.",
        "",
        "## 1. Reply-Intent Classification Accuracy (MEASURED)",
        "",
        "- Classifier: `app.adapters.reply_classifier.DeterministicReplyClassifier` (rule-based, no LLM)",
        f"- Dataset: {ri['dataset_size']} synthetic labeled B2B replies (`evaluation/datasets/reply_intent_cases.json`)",
        f"- Correct: {ri['correct']} / Incorrect: {ri['incorrect']}",
        f"- **Accuracy: {ri['accuracy'] * 100:.1f}%**",
        "",
        "| Label | Support | Precision | Recall |",
        "|---|---|---|---|",
    ]
    for label, m in ri["per_class_metrics"].items():
        prec = f"{m['precision']:.2f}" if m["precision"] is not None else "n/a"
        rec = f"{m['recall']:.2f}" if m["recall"] is not None else "n/a"
        lines.append(f"| {label} | {m['support']} | {prec} | {rec} |")

    lines += [
        "",
        "## 2. Human Approval Outcome Distribution (MEASURED, synthetic rubric)",
        "",
        f"- Dataset: {ap['dataset_size']} synthetic prospects (`evaluation/datasets/approval_prospects.json`)",
        f"- Approved as-is: {ap['approved_as_is']} ({ap['approved_as_is_pct']}%)",
        f"- Approved with edits: {ap['approved_with_edits']} ({ap['approved_with_edits_pct']}%)",
        f"- Rejected: {ap['rejected']} ({ap['rejected_pct']}%)",
        "",
        f"> {ap['caveat']}",
        "",
        "## 3. Automated Tests and Coverage (MEASURED)",
        "",
        f"- Backend: {bt['passed']} passed (pytest), line coverage: {bt['coverage_percent']}%",
        f"- Frontend: {ft['passed']} passed of {ft['total']} (vitest), coverage: not configured "
        f"({ft.get('test_file_count')} test files)",
        "",
        "## 4. Estimated Human Effort (ESTIMATE, not measured)",
        "",
        f"- Manual research + drafting: ~{ts['manual_minutes_range'][0]}-{ts['manual_minutes_range'][1]} min/prospect",
        f"- SalesOS human review/approval: ~{ts['salesos_minutes_range'][0]}-{ts['salesos_minutes_range'][1]} min/prospect",
        f"- {ts['note']}",
        "",
    ]

    (RESULTS_DIR / "salesos-results.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {RESULTS_DIR / 'salesos-results.md'}")


if __name__ == "__main__":
    main()
