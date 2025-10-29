"""
Basic test to ensure CI passes - minimal test suite.
"""


def test_basic_assertion():
    """A simple test that always passes."""
    assert True


def test_imports_work():
    """Test that basic Python imports work."""
    import os
    import sys
    assert os is not None
    assert sys is not None


def test_math_operations():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 10 > 5
    assert isinstance(42, int)