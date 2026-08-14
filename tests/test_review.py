"""Tests for the decisions taken about one folder of images."""

from __future__ import annotations

from pathlib import Path

from phototriage.review import Decision, Review, Verdict


def review(destination: Path) -> Review:
    return Review(destination=destination)


def test_decide_records_the_verdict(tmp_path: Path) -> None:
    subject = review(tmp_path)

    subject.decide("a.png", Verdict.KEEP)

    assert subject.decisions == [Decision("a.png", Verdict.KEEP)]


def test_verdicts_keeps_the_order_of_the_decisions(tmp_path: Path) -> None:
    subject = review(tmp_path)

    subject.decide("c.png", Verdict.KEEP)
    subject.decide("a.png", Verdict.DISCARD)
    subject.decide("b.png", Verdict.KEEP)

    assert list(subject.verdicts) == ["c.png", "a.png", "b.png"]
    assert subject.verdicts["a.png"] is Verdict.DISCARD


def test_undo_drops_only_the_last_decision(tmp_path: Path) -> None:
    subject = review(tmp_path)
    subject.decide("a.png", Verdict.KEEP)
    subject.decide("b.png", Verdict.DISCARD)

    subject.undo()

    assert list(subject.verdicts) == ["a.png"]


def test_undo_does_nothing_when_there_is_no_decision(tmp_path: Path) -> None:
    subject = review(tmp_path)

    subject.undo()

    assert subject.decisions == []


def test_two_reviews_do_not_share_a_decision_list(tmp_path: Path) -> None:
    first, second = review(tmp_path), review(tmp_path)

    first.decide("a.png", Verdict.KEEP)

    assert second.decisions == []
