import pytest

from agents_booking.catalog import CATALOG
from agents_booking.models import ShopState
from agents_booking.tools import ShopTools
from agents_booking.tracer import ToolTracer


@pytest.fixture
def catalog():
    return CATALOG


@pytest.fixture
def shop_tools(catalog):
    return ShopTools(catalog)


@pytest.fixture
def state():
    return ShopState()


@pytest.fixture
def tracer():
    return ToolTracer()
