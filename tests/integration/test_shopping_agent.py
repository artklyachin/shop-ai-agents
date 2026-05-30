import pytest

from agents_booking import CATALOG, TOOLS
from agents_booking.models import ShopState
from agents_booking.tracer import ToolTracer
from agents_booking.agents.shopping import run_shopping_agent
from tests.conftest import state

pytestmark = pytest.mark.integration


def test_search_with_price_filter():
    state = ShopState()
    tracer = ToolTracer()
    run_shopping_agent("Find wireless headphones under 150 dollars", state, TOOLS, tracer)
    
    assert tracer.called("search_products"), "search_products не был вызван"
    assert all(p["price"] <= 150 for p in state.last_results)


def test_search_and_add_cheapest_mouse():
    state = ShopState()
    tracer = ToolTracer()
    run_shopping_agent(
        "Find a wireless mouse under 120 dollars and add the cheapest one to cart",
        state, TOOLS, tracer,
    )

    assert tracer.called("search_products") and tracer.called("add_to_cart")
    assert len(state.cart) == 1
    assert state.cart[0]["product_id"] == "p7"


def test_find_best_keyboard_and_add_to_cart():
    state = ShopState()
    tracer = ToolTracer()
    run_shopping_agent(
        "Find a wireless keyboard with the best rating and add it to cart",
        state, TOOLS, tracer,
    )

    assert tracer.called("search_products") and tracer.called("add_to_cart")
    added = next(p for p in CATALOG if p["id"] == state.cart[0]["product_id"])
    assert added["category"] == "keyboard"
