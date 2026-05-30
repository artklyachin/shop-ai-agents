import pytest
from pathlib import Path

from agents_booking import TOOLS
from agents_booking.models import ShopState
from agents_booking.tracer import ToolTracer
from agents_booking.profile import load_profile, save_profile
from agents_booking.agents.memory import run_memory_agent

pytestmark = pytest.mark.integration


def test_saves_preferences_to_profile(tmp_path):
    profile_path = tmp_path / "profile.json"
    state = ShopState()
    tracer = ToolTracer()
    history = []

    run_memory_agent(
        "My name is Anna, I prefer Sony and my budget is 200 dollars",
        state, TOOLS, tracer, history, profile_path,
    )

    profile = load_profile(profile_path)
    assert tracer.called("update_profile")
    assert profile.get("brand") == "Sony"


def test_new_session_reads_profile(tmp_path):
    profile_path = tmp_path / "profile.json"
    save_profile({"name": "Boris", "brand": "Logitech", "max_price": "150"}, profile_path)

    state = ShopState()
    tracer = ToolTracer()
    history = []
    response, _ = run_memory_agent(
        "What is my name and what is my budget?",
        state, TOOLS, tracer, history, profile_path,
    )

    assert "Boris" in response


def test_short_term_memory_across_turns(tmp_path):
    profile_path = tmp_path / "profile.json"
    state = ShopState()
    history = []

    _, history = run_memory_agent(
        "Find wireless headphones under 150 dollars",
        state, TOOLS, ToolTracer(), history, profile_path,
    )
    assert len(history) >= 2

    tracer2 = ToolTracer()
    _, history = run_memory_agent(
        "Add the first one found to cart",
        state, TOOLS, tracer2, history, profile_path,
    )

    assert tracer2.called("add_to_cart")
    assert len(state.cart) == 1
