from sqlalchemy.dialects.sqlite import dialect

from hermes.enum import DayOfWeek, EmissionType, Enums


def test_enums_process_bind_params():
    enums = Enums(DayOfWeek)
    input_value = [DayOfWeek.Sun, DayOfWeek.Mon]
    expected_output = '["Sun", "Mon"]'

    result = enums.process_bind_param(input_value, dialect)
    assert result == expected_output


def test_enums_process_bind_param_none():
    enums = Enums(DayOfWeek)
    result = enums.process_bind_param(None, dialect)
    assert result is None


def test_enums_process_result_value():
    enums = Enums(EmissionType)
    input_value = '["A1A", "J3C"]'
    expected_output = [EmissionType.A1A, EmissionType.J3C]

    result = enums.process_result_value(input_value, dialect)
    assert result == expected_output


def test_enums_process_result_value_none():
    enums = Enums(EmissionType)
    result = enums.process_result_value(None, dialect)
    assert result is None
