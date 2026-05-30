import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from agents_booking.llm import llm_chat
from agents_booking.models import ShopState
from agents_booking.tools import ShopTools, SHOP_TOOLS_SCHEMA
from agents_booking.tracer import ToolTracer


def run_shopping_agent(
    user_message: str,
    state: ShopState,
    tools: ShopTools,
    tracer: ToolTracer,
) -> str:
    """
    ReAct-агент магазина. Получает сообщение пользователя и итеративно:
      1. Вызывает LLM с историей и схемой инструментов.
      2. Если LLM вернул tool_calls — выполняет каждый инструмент и продолжает цикл.
      3. Если tool_calls пусто — возвращает текстовый ответ LLM.
    """
    history = [
        SystemMessage(content="Ты полезный помощник по покупкам. Используй инструменты для поиска товаров и добавления в корзину."),
        HumanMessage(content=user_message),
    ]

    for _ in range(10):
        response = llm_chat(history, SHOP_TOOLS_SCHEMA)
        if not response:
            raise ValueError("Пустой ответ от LLM")

        history.append(AIMessage(content=response.content, tool_calls=response.tool_calls or []))

        finish_reason = response.response_metadata.get("finish_reason")
        if finish_reason == "stop":
            return response.content
        elif finish_reason == "tool_calls":
            for call in response.tool_calls:
                if call["name"] == "search_products":
                    result = tools.search_products(**call["args"])
                    state.last_results = result
                    tracer.record("search_products", call["args"], result)
                    history.append(ToolMessage(content=json.dumps(result), tool_call_id=call["id"]))
                elif call["name"] == "add_to_cart":
                    result = tools.add_to_cart(state, **call["args"])
                    tracer.record("add_to_cart", call["args"], result)
                    history.append(ToolMessage(content=json.dumps(result), tool_call_id=call["id"]))
                else:
                    raise ValueError(f"Неизвестный инструмент: {call['name']}")
        else:
            raise ValueError(f"Неожиданный finish_reason: {finish_reason}")

    raise RuntimeError("Превышен лимит итераций цикла")
