from app.adapters.reply_classifier import DeterministicReplyClassifier


def test_classify_unsubscribe_opt_out() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("Please unsubscribe me from this mailing list.", "Re: Partnership"),
        ("Take me off your list and stop emailing me.", "Re: Follow up"),
        ("Do not contact me again, not interested.", "Re: Solution demo"),
        ("Remove me immediately.", "Re: Quick question"),
        ("Please opt out this email.", "Re: SalesOS"),
        ("Please leave me alone.", "Re: Intro"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "unsubscribe"
        assert result.sentiment == "negative"
        assert result.needs_human_action is True
        assert result.confidence_score >= 0.90


def test_classify_out_of_office() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("I am currently out of the office on annual leave until next Monday.", "Automatic reply: Out of office"),
        ("Thank you for your email. I am away from my desk on vacation.", "Auto-reply: Vacation"),
        ("I am currently on maternity leave returning in November.", "Auto: Leave notice"),
        ("Automatic reply: I will be returning on Tuesday.", "Auto Response"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "out_of_office"
        assert result.sentiment == "neutral"
        assert result.needs_human_action is False
        assert result.confidence_score >= 0.85


def test_classify_referral() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("I am looping in Sarah who leads our infrastructure engineering.", "Re: Core API migration"),
        ("Please refer you to my colleague Alex, cc'd here.", "Re: Intro"),
        ("You should speak with Jane regarding B2B sales tooling.", "Re: SalesOS intro"),
        ("Forwarded to our VP of Sales.", "Re: Outbound automation"),
        ("The right person would be Dave in DevOps.", "Re: Infrastructure check"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "referral"
        assert result.sentiment == "positive"
        assert result.needs_human_action is False
        assert result.confidence_score >= 0.80


def test_classify_objection() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("We are happy with our current vendor and not a good fit right now.", "Re: Demo inquiry"),
        ("This is too expensive for our current stage.", "Re: Pricing"),
        ("We already use CompetitorX for all our outbound sales.", "Re: AI Outreach"),
        ("We have a long-term contract with another platform.", "Re: Sales platform"),
        ("We don't need any new sales software.", "Re: Solution"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "objection"
        assert result.sentiment == "negative"
        assert result.needs_human_action is True
        assert result.confidence_score >= 0.80


def test_classify_not_now() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("Not right now, please check back next quarter.", "Re: Introduction"),
        ("Bad timing for us, busy right now with product launch.", "Re: Connecting"),
        ("No budget allocated for this half, check back in Q4.", "Re: Quick chat"),
        ("Circling back later would be better, reach back out in 3 months.", "Re: Follow-up"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "not_now"
        assert result.sentiment == "neutral"
        assert result.needs_human_action is False
        assert result.confidence_score >= 0.75


def test_classify_interested() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("Sounds good, let's schedule a demo call.", "Re: SalesOS"),
        ("Interested in this! Please send over more info.", "Re: AI platform"),
        ("Open to connecting. I am free on Thursday afternoon.", "Re: Catching up"),
        ("Here is my calendar link, let's book time to chat.", "Re: Meeting"),
        ("Let's set up a call next week.", "Re: Platform overview"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "interested"
        assert result.sentiment == "positive"
        assert result.needs_human_action is False
        assert result.confidence_score >= 0.80


def test_classify_question() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("How much does the enterprise tier cost?", "Re: Pricing"),
        ("What is your pricing model for 50 SDR seats?", "Re: Information"),
        ("Can you explain how this integrates with HubSpot CRM?", "Re: Integrations"),
        ("Do you integrate with Postgres directly?", "Re: Technical specs"),
        ("Could you tell me more about your compliance guarantees?", "Re: Security"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "question"
        assert result.sentiment == "neutral"
        assert result.needs_human_action is True
        assert result.confidence_score >= 0.75


def test_classify_ambiguous_fallback() -> None:
    classifier = DeterministicReplyClassifier()

    cases = [
        ("Thanks.", "Re: Quick question"),
        ("Noted.", "Re: Update"),
        ("Understood, will take a look.", "Re: Info"),
    ]

    for body, subj in cases:
        result = classifier.classify(body, subj)
        assert result.reply_state == "ambiguous"
        assert result.sentiment == "neutral"
        assert result.needs_human_action is True
        assert result.confidence_score == 0.40


def test_classification_priority_order() -> None:
    classifier = DeterministicReplyClassifier()

    # Unsubscribe phrase with out of office -> Unsubscribe wins
    res1 = classifier.classify("I am out of the office. Please unsubscribe me and stop emailing.", "Auto Reply")
    assert res1.reply_state == "unsubscribe"
    assert res1.sentiment == "negative"

    # Out of office with referral phrase -> Out of office wins
    res2 = classifier.classify("I am out of the office on vacation, speak with my colleague.", "Auto Reply")
    assert res2.reply_state == "out_of_office"

    # Objection with timing phrase -> Objection wins
    res3 = classifier.classify("Too expensive for us, not right now.", "Re: Outreach")
    assert res3.reply_state == "objection"
