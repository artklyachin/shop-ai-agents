import copy

from langchain_core.utils.function_calling import convert_to_openai_tool

from agents_booking.models import ShopState


class ShopTools:
    """Бизнес-логика магазина: поиск товаров и управление корзиной."""

    def __init__(self, catalog: list):
        self.catalog = catalog

    def search_products(
        self,
        query: str = "",
        category: str | None = None,
        brand: str | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
    ) -> list:
        results = []
        q_words = query.lower().split() if query else []
        for item in self.catalog:
            hay = f"{item['name']} {item['category']} {item['brand']} {' '.join(item['tags'])}".lower()
            if q_words and not all(w in hay for w in q_words):
                continue
            if category and item["category"] != category:
                continue
            if brand and item["brand"].lower() != brand.lower():
                continue
            if max_price is not None and item["price"] > float(max_price):
                continue
            results.append(copy.deepcopy(item))
        if sort_by == "price_asc":
            results.sort(key=lambda x: x["price"])
        elif sort_by == "rating_desc":
            results.sort(key=lambda x: -x["rating"])
        return results

    def add_to_cart(self, state: ShopState, product_id: str, quantity: int = 1) -> dict:
        product = next((p for p in self.catalog if p["id"] == product_id), None)
        if not product:
            return {"ok": False, "error": f"Product {product_id} not found"}
        existing = next((r for r in state.cart if r["product_id"] == product_id), None)
        if existing:
            existing["quantity"] += quantity
        else:
            state.cart.append({
                "product_id": product_id,
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
            })
        return {"ok": True, "cart_size": len(state.cart)}


# --- Stub-функции для генерации схем инструментов ---

def search_products(
    query: str = "",
    category: str | None = None,
    brand: str | None = None,
    max_price: float | None = None,
    sort_by: str | None = None,
) -> list:
    """Ищет товары в каталоге по заданным критериям.

    Args:
        query: поисковый запрос (ключевые слова).
        category: фильтр по категории (headphones, earbuds, mouse, keyboard, ereader).
        brand: фильтр по бренду.
        max_price: максимальная цена.
        sort_by: сортировка — price_asc или rating_desc.
    """
    ...


def add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """Добавляет товар в корзину покупок.

    Args:
        product_id: идентификатор товара (например, p1, p2).
        quantity: количество единиц товара.
    """
    ...


SHOP_TOOLS_SCHEMA = [
    convert_to_openai_tool(search_products),
    convert_to_openai_tool(add_to_cart),
]
