import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

load_dotenv()

YANDEX_FOLDER_ID = os.environ["YANDEX_FOLDER_ID"]
YANDEX_API_KEY = os.environ["YANDEX_API_KEY"]
MODEL_NAME = "gpt-oss-20b"

llm = ChatOpenAI(
    model=f"gpt://{YANDEX_FOLDER_ID}/{MODEL_NAME}",
    api_key=YANDEX_API_KEY,
    base_url="https://ai.api.cloud.yandex.net/v1",
    temperature=0,
)


def llm_chat(messages: list, tools: list | None = None) -> AIMessage:
    """
    Отправляет историю сообщений в LLM и возвращает ответ модели.

    Args:
        messages: список объектов LangChain (SystemMessage, HumanMessage, AIMessage, ToolMessage).
        tools: список описаний инструментов (OpenAI function calling schema или LangChain tools).

    Returns:
        AIMessage с полями content (текст) и tool_calls (список вызовов инструментов).
    """
    if tools:
        return llm.bind_tools(tools).invoke(messages)
    return llm.invoke(messages)
