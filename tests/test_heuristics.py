from heuristics import calculate_local_risk_score, detect_red_flags


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


def test_calculate_local_risk_score_without_flags() -> None:
    result = calculate_local_risk_score("Работа с документами и внутренними системами.")

    assert result["risk_score"] == 0
    assert result["risk_level"] == "low"
    assert result["red_flags"] == []
    assert "не найдены" in result["summary"]


def test_calculate_local_risk_score_with_light_flags() -> None:
    result = calculate_local_risk_score("В вакансии обещают быстрый карьерный рост и высокий стресс.")

    assert 0 < result["risk_score"] < 6
    assert result["risk_level"] in {"low", "medium"}
    assert "быстрый карьерный рост" in result["red_flags"]
    assert "высокий стресс" in result["red_flags"]


def test_calculate_local_risk_score_with_serious_flags() -> None:
    result = calculate_local_risk_score("Нужны активные продажи, холодные звонки и личный автомобиль.")

    assert result["risk_score"] >= 6
    assert result["risk_level"] == "high"
    assert "активные продажи" in result["red_flags"]
    assert "холодные звонки" in result["red_flags"]
    assert "личный автомобиль" in result["red_flags"]


def test_calculate_local_risk_score_is_capped_at_10() -> None:
    text = """
    Активные продажи, холодные звонки, зарплата только процентом,
    личный автомобиль, курьер, грузчик, план продаж, поиск клиентов.
    """

    result = calculate_local_risk_score(text)

    assert result["risk_score"] == 10


def test_calculate_local_risk_score_uses_custom_json_weights(tmp_path) -> None:
    weights_path = tmp_path / "risk_weights.json"
    weights_path.write_text('{"fast_career_growth": 6}', encoding="utf-8")

    result = calculate_local_risk_score(
        "В вакансии обещают быстрый карьерный рост.",
        weights_path=weights_path,
    )

    assert result["risk_score"] == 6
    assert result["risk_level"] == "high"


def test_calculate_local_risk_score_falls_back_when_weights_json_is_invalid(tmp_path) -> None:
    weights_path = tmp_path / "risk_weights.json"
    weights_path.write_text("{bad json", encoding="utf-8")

    result = calculate_local_risk_score(
        "В вакансии обещают быстрый карьерный рост.",
        weights_path=weights_path,
    )

    assert result["risk_score"] == 1
    assert result["risk_level"] == "low"
