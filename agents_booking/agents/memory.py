import json
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

from agents_booking.llm import llm_chat
from agents_booking.models import ShopState
from agents_booking.tools import ShopTools, SHOP_TOOLS_SCHEMA
from agents_booking.tracer import ToolTracer
from agents_booking.profile import load_profile, save_profile, update_profile, PROFILE_PATH

SHOP_TOOLS_SCHEMA_WITH_MEMORY = [
    *SHOP_TOOLS_SCHEMA,
    convert_to_openai_tool(update_profile),
]


def run_memory_agent(
    user_message: str,
    state: ShopState,
    tools: ShopTools,
    tracer: ToolTracer,
    history: list,
    profile_path: Path = PROFILE_PATH,
) -> tuple:
    """
    Агент с памятью. Расширяет run_shopping_agent долгосрочной и краткосрочной памятью.

    Долгосрочная память:
      - Загружает профиль из файла (load_profile) при каждом запуске
      - Передаёт профиль агенту через SystemMessage
      - Инструмент update_profile обновляет профиль на диске

    Краткосрочная память:
      - history содержит полную историю сообщений из предыдущих ходов
      - Позволяет агенту «видеть» результаты прошлых поисков в следующем ходе

    Returns:
        Кортеж (response: str, updated_history: list).
    """
    history.append(HumanMessage(content=user_message))

    def make_system_message():
        profile = load_profile(profile_path)
        return SystemMessage(
            content=(
                "Ты полезный помощник по покупкам. Используй инструменты для поиска товаров и добавления в корзину."
                f" Профиль пользователя: {json.dumps(profile, ensure_ascii=False)}"
            )
        )

    for _ in range(10):
        response = llm_chat([make_system_message(), *history], SHOP_TOOLS_SCHEMA_WITH_MEMORY)
        if not response:
            raise ValueError("Пустой ответ от LLM")

        history.append(AIMessage(content=response.content, tool_calls=response.tool_calls or []))

        finish_reason = response.response_metadata.get("finish_reason")
        if finish_reason == "stop":
            return response.content, history
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
                elif call["name"] == "update_profile":
                    profile = load_profile(profile_path)
                    profile[call["args"]["key"]] = call["args"]["value"]
                    save_profile(profile, profile_path)
                    tracer.record("update_profile", call["args"], profile)
                    history.append(ToolMessage(content=json.dumps(profile, ensure_ascii=False), tool_call_id=call["id"]))
                else:
                    raise ValueError(f"Неизвестный инструмент: {call['name']}")
        else:
            raise ValueError(f"Неожиданный finish_reason: {finish_reason}")

    raise RuntimeError("Превышен лимит итераций цикла")
