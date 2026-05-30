import pytest

from agents_booking import TOOLS
from agents_booking.models import ShopState
from agents_booking.agents.coordinator import CoordinatorAgent

pytestmark = pytest.mark.integration


def test_full_cycle_search_analyze_rank_cart():
    state = ShopState()
    result = CoordinatorAgent().run(
        "Find the best wireless mouse under 120 dollars and add it to cart",
        state, TOOLS,
    )

    assert "delegate_retriever" in result.trace
    assert "delegate_pros" in result.trace
    assert "delegate_cons" in result.trace
    assert "delegate_ranker" in result.trace
    assert "delegate_cart" in result.trace

    assert len(state.cart) == 1
    assert state.cart[0]["product_id"] == "p6"

    assert result.context.best is not None
    assert result.context.best["id"] == "p6"
    assert len(result.context.pros) > 0
    assert len(result.context.cons) > 0
