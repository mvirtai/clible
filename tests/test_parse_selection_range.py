"""
Tests for parse_selection_range function.

Verifies that the range parsing function correctly handles various input formats
including single numbers, ranges, and mixed inputs.
"""

import pytest
from unittest.mock import Mock, patch
from app.menus.menu_utils import parse_selection_range


class TestParseSelectionRange:
    """Tests for parse_selection_range function"""

    def test_single_number(self):
        """Test parsing a single number"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("5", 10)
            assert result == [5]
            mock_console.print.assert_not_called()

    def test_multiple_numbers(self):
        """Test parsing multiple comma-separated numbers"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1,3,5", 10)
            assert result == [1, 3, 5]
            mock_console.print.assert_not_called()

    def test_simple_range(self):
        """Test parsing a simple range"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1-5", 10)
            assert result == [1, 2, 3, 4, 5]
            mock_console.print.assert_not_called()

    def test_mixed_numbers_and_ranges(self):
        """Test parsing mixed numbers and ranges"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1-3, 7, 10-12", 15)
            assert result == [1, 2, 3, 7, 10, 11, 12]
            mock_console.print.assert_not_called()

    def test_range_with_spaces(self):
        """Test parsing range with spaces around commas"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1 - 3 , 5 , 7 - 9", 10)
            assert result == [1, 2, 3, 5, 7, 8, 9]
            mock_console.print.assert_not_called()

    def test_invalid_range_start_too_low(self):
        """Test that range starting below 1 is rejected"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("0-5", 10)
            assert result is None
            mock_console.print.assert_called_once()

    def test_invalid_range_end_too_high(self):
        """Test that range ending above max_value is rejected"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1-15", 10)
            assert result is None
            mock_console.print.assert_called_once()

    def test_invalid_single_value_too_low(self):
        """Test that single value below 1 is rejected"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("0", 10)
            assert result is None
            mock_console.print.assert_called_once()

    def test_invalid_single_value_too_high(self):
        """Test that single value above max_value is rejected"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("15", 10)
            assert result is None
            mock_console.print.assert_called_once()

    def test_invalid_non_numeric_value(self):
        """Test that non-numeric values are rejected"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("abc", 10)
            assert result is None
            mock_console.print.assert_called_once()

    def test_empty_string(self):
        """Test that empty string returns empty list"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("", 10)
            assert result == []
            mock_console.print.assert_not_called()

    def test_string_with_only_spaces(self):
        """Test that string with only spaces returns empty list"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("   ,  ,  ", 10)
            assert result == []
            mock_console.print.assert_not_called()

    def test_range_at_max_boundary(self):
        """Test that range ending at max_value is accepted"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("8-10", 10)
            assert result == [8, 9, 10]
            mock_console.print.assert_not_called()

    def test_single_value_at_max_boundary(self):
        """Test that single value at max_value is accepted"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("10", 10)
            assert result == [10]
            mock_console.print.assert_not_called()

    def test_complex_mixed_input(self):
        """Test complex input with multiple ranges and numbers"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1-3, 5, 7-9, 11, 13-15", 20)
            assert result == [1, 2, 3, 5, 7, 8, 9, 11, 13, 14, 15]
            mock_console.print.assert_not_called()

    def test_reverse_range(self):
        """Test that reverse range (end < start) is handled"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("5-3", 10)
            # Should still work but produce empty range
            assert result == []
            mock_console.print.assert_not_called()

    def test_partial_invalid_input(self):
        """Test that partial invalid input causes function to return None"""
        with patch('app.menus.menu_utils.console') as mock_console:
            result = parse_selection_range("1-3, 15, 5-7", 10)
            # Should fail because 15 > 10
            assert result is None
            mock_console.print.assert_called_once()

