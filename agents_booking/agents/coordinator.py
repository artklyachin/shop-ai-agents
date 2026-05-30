import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

from agents_booking.llm import llm_chat
from agents_booking.models import ShopState, AgentContext, AgentResult
from agents_booking.tools import ShopTools, search_products
from agents_booking.tracer import ToolTracer


def record_pros(pros: str) -> dict:
    """Записывает плюсы товара.

    Args:
        pros: 1-2 предложения о преимуществах товара.
    """
    ...


def record_cons(cons: str) -> dict:
    """Записывает минусы товара.

    Args:
        cons: 1-2 предложения о недостатках товара.
    """
    ...


class RetrieverAgent:
    """Ищет до 5 релевантных товаров через LLM + инструменты."""

    TOOLS_SCHEMA = [convert_to_openai_tool(search_products)]

    def run(self, ctx: AgentContext, state: ShopState, tools: ShopTools, tracer: ToolTracer) -> AgentContext:
        history = [
            SystemMessage(content="Ты помощник по поиску товаров. Найди товары по запросу пользователя. Когда получишь достаточно результатов, останови поиск и ответь 'done'."),
            HumanMessage(content=ctx.query),
        ]

        all_results = []
        seen_ids: set = set()

        for _ in range(4):
            response = llm_chat(history, self.TOOLS_SCHEMA)
            history.append(AIMessage(content=response.content, tool_calls=response.tool_calls or []))

            finish_reason = response.response_metadata.get("finish_reason")
            if finish_reason == "stop":
                break
            elif finish_reason == "tool_calls":
                for call in response.tool_calls:
                    valid_keys = {"query", "category", "brand", "max_price", "sort_by"}
                    result = tools.search_products(**{k: v for k, v in call["args"].items() if k in valid_keys})
                    tracer.record("search_products", call["args"], result)
                    history.append(ToolMessage(content=json.dumps(result), tool_call_id=call["id"]))

                    if ctx.max_price is None and call["args"].get("max_price") is not None:
                        ctx.max_price = float(call["args"]["max_price"])

                    for product in result:
                        if product["id"] not in seen_ids:
                            seen_ids.add(product["id"])
                            all_results.append(product)

                if len(all_results) >= 5:
                    break
            else:
                raise ValueError(f"Неожиданный finish_reason: {finish_reason}")

        ctx.candidates = all_results[:5]
        return ctx


class ProsAgent:
    """Описывает преимущества каждого товара через LLM."""

    TOOLS_SCHEMA = [convert_to_openai_tool(record_pros)]

    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        for product in ctx.candidates:
            response = llm_chat([
                SystemMessage(content="Ты ОБЯЗАН вызвать инструмент record_pros с 1-2 предложениями о преимуществах товара, релевантных запросу пользователя. Не отвечай текстом."),
                HumanMessage(content=f"Запрос пользователя: {ctx.query}\n\nТовар: {json.dumps(product, ensure_ascii=False)}"),
            ], self.TOOLS_SCHEMA)

            if response.tool_calls:
                ctx.pros[product["id"]] = response.tool_calls[0]["args"]["pros"]
            else:
                ctx.pros[product["id"]] = response.content

        tracer.record("analyze_pros", {"candidates": [p["id"] for p in ctx.candidates]}, ctx.pros)
        return ctx


class ConsAgent:
    """Описывает недостатки каждого товара через LLM."""

    TOOLS_SCHEMA = [convert_to_openai_tool(record_cons)]

    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        for product in ctx.candidates:
            response = llm_chat([
                SystemMessage(content="Ты ОБЯЗАН вызвать инструмент record_cons с 1-2 предложениями о недостатках товара, релевантных запросу пользователя. Не отвечай текстом."),
                HumanMessage(content=f"Запрос пользователя: {ctx.query}\n\nТовар: {json.dumps(product, ensure_ascii=False)}"),
            ], self.TOOLS_SCHEMA)

            if response.tool_calls:
                ctx.cons[product["id"]] = response.tool_calls[0]["args"]["cons"]
            else:
                ctx.cons[product["id"]] = response.content

        tracer.record("analyze_cons", {"candidates": [p["id"] for p in ctx.candidates]}, ctx.cons)
        return ctx


class RankerAgent:
    """Выбирает лучший товар из кандидатов (без LLM — чистая логика)."""

    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        candidates = ctx.candidates
        if ctx.max_price is not None:
            candidates = [p for p in candidates if p["price"] <= ctx.max_price]
        if candidates:
            ctx.best = min(candidates, key=lambda p: (-p["rating"], p["price"]))
        tracer.record("rank_candidates", {"max_price": ctx.max_price}, ctx.best)
        return ctx


class CoordinatorAgent:
    """
    Оркестратор. Запускает агентов в цепочке:
    Retriever → Pros → Cons → Ranker → (опционально) добавление в корзину.
    """

    def __init__(self):
        self.retriever = RetrieverAgent()
        self.pros_agent = ProsAgent()
        self.cons_agent = ConsAgent()
        self.ranker = RankerAgent()

    def run(self, user_message: str, state: ShopState, tools: ShopTools) -> AgentResult:
        tracer = ToolTracer()
        trace = []
        ctx = AgentContext(query=user_message)

        trace.append("delegate_retriever")
        ctx = self.retriever.run(ctx, state, tools, tracer)

        trace.append("delegate_pros")
        ctx = self.pros_agent.run(ctx, tracer)

        trace.append("delegate_cons")
        ctx = self.cons_agent.run(ctx, tracer)

        trace.append("delegate_ranker")
        ctx = self.ranker.run(ctx, tracer)

        if ctx.best and "cart" in user_message.lower():
            trace.append("delegate_cart")
            tools.add_to_cart(state, product_id=ctx.best["id"])

        if not ctx.best:
            response = "Товары по вашему запросу не найдены."
        else:
            p = ctx.best
            pros = ctx.pros.get(p["id"], "")
            cons = ctx.cons.get(p["id"], "")
            response = (
                f"Лучший выбор: {p['name']} — ${p['price']} (рейтинг {p['rating']})\n"
                f"Плюсы: {pros}\n"
                f"Минусы: {cons}"
            )

        return AgentResult(response=response, trace=trace, context=ctx)
