from code_to_optimize.pie_test_set.p02957 import problem_p02957


def test_problem_p02957_0():
    actual_output = problem_p02957("2 16")
    expected_output = "9"
    assert str(actual_output) == expected_output


def test_problem_p02957_1():
    actual_output = problem_p02957("998244353 99824435")
    expected_output = "549034394"
    assert str(actual_output) == expected_output


def test_problem_p02957_2():
    actual_output = problem_p02957("0 3")
    expected_output = "IMPOSSIBLE"
    assert str(actual_output) == expected_output


def test_problem_p02957_3():
    actual_output = problem_p02957("2 16")
    expected_output = "9"
    assert str(actual_output) == expected_output
