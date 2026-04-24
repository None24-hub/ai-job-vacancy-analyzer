from heuristics import detect_red_flags


def test_detect_red_flags_finds_known_risks_case_insensitively() -> None:
    text = """
    Работа предполагает холодные звонки, активные продажи и план продаж.
    Нужен личный автомобиль. Доход без потолка, научим зарабатывать.
    """

    flags = detect_red_flags(text)

    assert "холодные звонки" in flags
    assert "активные продажи" in flags
    assert "план продаж" in flags
    assert "личный автомобиль" in flags
    assert "доход без потолка" in flags
    assert "научим зарабатывать" in flags


def test_detect_red_flags_returns_empty_list_when_no_flags_found() -> None:
    text = "Работа с документами, таблицами и внутренними системами. Обучение на месте."

    assert detect_red_flags(text) == []
