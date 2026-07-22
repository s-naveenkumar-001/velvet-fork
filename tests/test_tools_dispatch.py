import tool_schemas


def test_dispatch_unknown_tool_name_returns_error_dict_not_raise(db_session):
    result = tool_schemas.call_tool("not_a_real_tool", {})
    assert result["error"] == "unknown_tool"


def test_dispatch_bad_arguments_returns_error_dict_not_raise(db_session):
    result = tool_schemas.call_tool("get_menu", {"unexpected_kwarg": "x"})
    assert result["error"] == "invalid_arguments"


def test_get_menu_filters_by_category(db_session):
    result = tool_schemas.call_tool("get_menu", {"category": "Pizza"})
    names = [item["name"] for item in result["items"]]
    assert names == ["Test Pizza"]


def test_get_restaurant_info_returns_exact_grounding_text(db_session):
    result = tool_schemas.call_tool("get_restaurant_info", {"topic": "hours"})
    import restaurant_info

    assert result["text"] == restaurant_info.HOURS_TEXT


def test_get_restaurant_info_invalid_topic_returns_error(db_session):
    result = tool_schemas.call_tool("get_restaurant_info", {"topic": "not_a_topic"})
    assert result["error"] == "invalid_topic"
