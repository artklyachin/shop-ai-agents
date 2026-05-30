from agents_booking.tracer import ToolTracer


def test_record_and_called(tracer):
    tracer.record("search_products", {"query": "mouse"}, [{"id": "p6"}])
    assert tracer.called("search_products") is True


def test_called_false_for_unrecorded(tracer):
    assert tracer.called("add_to_cart") is False


def test_get_calls_filters_by_name(tracer):
    tracer.record("search_products", {"query": "mouse"})
    tracer.record("add_to_cart", {"product_id": "p6"})
    tracer.record("search_products", {"query": "keyboard"})

    calls = tracer.get_calls("search_products")
    assert len(calls) == 2
    assert all(c.name == "search_products" for c in calls)


def test_record_preserves_args_and_result(tracer):
    args = {"query": "headphones", "max_price": 200}
    result = [{"id": "p2"}]
    tracer.record("search_products", args, result)

    call = tracer.calls[0]
    assert call.args == args
    assert call.result == result


def test_multiple_records_order_preserved(tracer):
    tracer.record("search_products", {})
    tracer.record("add_to_cart", {})
    tracer.record("search_products", {})

    assert [c.name for c in tracer.calls] == ["search_products", "add_to_cart", "search_products"]
