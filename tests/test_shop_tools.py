import pytest

from agents_booking.models import ShopState
from agents_booking.tools import ShopTools


def test_search_returns_all_without_filters(shop_tools):
    results = shop_tools.search_products()
    assert len(results) == 10


def test_search_by_category(shop_tools):
    results = shop_tools.search_products(category="mouse")
    assert len(results) == 2
    assert all(r["category"] == "mouse" for r in results)


def test_search_by_brand(shop_tools):
    results = shop_tools.search_products(brand="Sony")
    assert len(results) == 2
    assert all(r["brand"] == "Sony" for r in results)


def test_search_by_max_price(shop_tools):
    results = shop_tools.search_products(max_price=100)
    assert all(r["price"] <= 100 for r in results)
    assert len(results) > 0


def test_search_by_query(shop_tools):
    results = shop_tools.search_products(query="wireless keyboard")
    assert all("keyboard" in r["category"] or "wireless" in r["tags"] for r in results)


def test_search_sort_price_asc(shop_tools):
    results = shop_tools.search_products(sort_by="price_asc")
    prices = [r["price"] for r in results]
    assert prices == sorted(prices)


def test_search_sort_rating_desc(shop_tools):
    results = shop_tools.search_products(sort_by="rating_desc")
    ratings = [r["rating"] for r in results]
    assert ratings == sorted(ratings, reverse=True)


def test_search_no_results(shop_tools):
    results = shop_tools.search_products(query="nonexistent product xyz")
    assert results == []


def test_add_to_cart_new_product(shop_tools, state):
    result = shop_tools.add_to_cart(state, product_id="p1")
    assert result["ok"] is True
    assert result["cart_size"] == 1
    assert state.cart[0]["product_id"] == "p1"
    assert state.cart[0]["quantity"] == 1


def test_add_to_cart_increases_quantity(shop_tools, state):
    shop_tools.add_to_cart(state, product_id="p1", quantity=2)
    shop_tools.add_to_cart(state, product_id="p1", quantity=3)
    assert len(state.cart) == 1
    assert state.cart[0]["quantity"] == 5


def test_add_to_cart_multiple_products(shop_tools, state):
    shop_tools.add_to_cart(state, product_id="p1")
    shop_tools.add_to_cart(state, product_id="p6")
    assert len(state.cart) == 2


def test_add_to_cart_unknown_product(shop_tools, state):
    result = shop_tools.add_to_cart(state, product_id="unknown")
    assert result["ok"] is False
    assert "error" in result
    assert len(state.cart) == 0
