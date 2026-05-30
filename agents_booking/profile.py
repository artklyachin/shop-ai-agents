import json
from pathlib import Path

PROFILE_PATH = Path("user_profile.json")

PROFILE_ALLOWED_KEYS = {"name", "brand", "max_price", "color", "category"}


def load_profile(path: Path = PROFILE_PATH) -> dict:
    """Загружает профиль из JSON. Возвращает {} если файл не существует."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_profile(profile: dict, path: Path = PROFILE_PATH) -> None:
    """Сохраняет профиль в файл JSON (только разрешённые ключи)."""
    filtered = {k: v for k, v in profile.items() if k in PROFILE_ALLOWED_KEYS}
    path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")


def update_profile(key: str, value: str) -> dict:
    """Сохраняет предпочтение пользователя в долгосрочный профиль.

    Args:
        key: поле профиля. Допустимые значения: name (имя пользователя),
            brand (предпочитаемый бренд), max_price (максимальная цена),
            color (предпочитаемый цвет), category (интересующая категория).
        value: значение для сохранения.
    """
    ...
