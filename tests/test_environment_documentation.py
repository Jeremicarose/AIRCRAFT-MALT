from tools.check_environment_documentation import undocumented_variables


def test_every_environment_variable_read_by_application_code_is_documented():
    assert undocumented_variables() == []
