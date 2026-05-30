import pytest

from agents_booking.models import AgentContext
from agents_booking.tracer import ToolTracer
from agents_booking.agents.coordinator import RankerAgent


def make_ctx(candidates, max_price=None):
    ctx = AgentContext(query="test")
    ctx.candidates = candidates
    ctx.max_price = max_price
    return ctx


def test_picks_highest_rating(tracer):
    ctx = make_ctx([
        {"id": "a", "name": "A", "price": 100, "rating": 4.5},
        {"id": "b", "name": "B", "price": 100, "rating": 4.8},
        {"id": "c", "name": "C", "price": 100, "rating": 4.2},
    ])
    ctx = RankerAgent().run(ctx, tracer)
    assert ctx.best["id"] == "b"


def test_tiebreak_by_lowest_price(tracer):
    ctx = make_ctx([
        {"id": "a", "name": "A", "price": 200, "rating": 4.8},
        {"id": "b", "name": "B", "price": 150, "rating": 4.8},
        {"id": "c", "name": "C", "price": 100, "rating": 4.5},
    ])
    ctx = RankerAgent().run(ctx, tracer)
    assert ctx.best["id"] == "b"


def test_respects_max_price(tracer):
    ctx = make_ctx([
        {"id": "expensive", "name": "Super", "price": 200, "rating": 4.9},
        {"id": "p6", "name": "MX Master", "price": 109, "rating": 4.8},
        {"id": "p7", "name": "Pebble 2",  "price": 34,  "rating": 4.2},
    ], max_price=120.0)
    ctx = RankerAgent().run(ctx, tracer)
    assert ctx.best["id"] == "p6"


def test_empty_after_price_filter(tracer):
    ctx = make_ctx([
        {"id": "a", "name": "A", "price": 300, "rating": 4.9},
    ], max_price=100.0)
    ctx = RankerAgent().run(ctx, tracer)
    assert ctx.best is None


def test_records_tracer_call(tracer):
    ctx = make_ctx([{"id": "a", "name": "A", "price": 50, "rating": 4.0}])
    RankerAgent().run(ctx, tracer)
    assert tracer.called("rank_candidates")


def test_empty_candidates(tracer):
    ctx = make_ctx([])
    ctx = RankerAgent().run(ctx, tracer)
    assert ctx.best is None
