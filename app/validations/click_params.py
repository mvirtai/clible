"""
Click parameter types for validating user input.

These custom parameter types integrate with Click's prompt system to provide
validation and clear error messages for book, chapter, and verse inputs.
"""

import click

from app.validations.validations import validate_books, validate_chapter, validate_verses


class BookParam(click.ParamType):
    """Click parameter type for validating book names."""
    name = "book"

    def convert(self, value, param, ctx):
        """
        Convert and validate book input.

        Args:
            value: Raw input value from user
            param: Click parameter object
            ctx: Click context

        Returns:
            Normalized book name (title case)

        Raises:
            click.BadParameter: If book is invalid
        """
        normalized = value.strip().lower()
        if validate_books(normalized):
            return normalized.title()
        self.fail(f"Unknown book: {value}", param, ctx)


class ChapterParam(click.ParamType):
    """
    Click parameter type for validating chapter numbers.

    Chapter must be a numeric value between 1 and 150.
    Empty input is not allowed.
    """
    name = "chapter"

    def convert(self, value, param, ctx):
        """
        Convert and validate chapter input.

        Args:
            value: Raw input value from user
            param: Click parameter object
            ctx: Click context

        Returns:
            Validated chapter string

        Raises:
            click.BadParameter: If chapter is invalid or empty
        """
        if value is None:
            value = ""

        normalized = value.strip()
        is_valid, payload = validate_chapter(normalized, allow_all=True)
        if is_valid:
            return payload
        self.fail(payload, param, ctx)


class VersesParam(click.ParamType):
    """
    Click parameter type for validating verse inputs.

    Verses can be:
    - Single verse: "1"
    - Range: "1-3"
    - Multiple: "1,3,5"
    - Mixed: "1-3,5-7"

    Empty input is allowed (for fetching entire chapter).
    """
    name = "verses"

    def __init__(self, allow_empty: bool = True):
        """
        Initialize VersesParam.

        Args:
            allow_empty: If True, empty string is considered valid (default: True)
        """
        super().__init__()
        self.allow_empty = allow_empty

    def convert(self, value, param, ctx):
        """
        Convert and validate verses input.

        Args:
            value: Raw input value from user (can be None or empty string)
            param: Click parameter object
            ctx: Click context

        Returns:
            Validated verses string (empty string if allow_empty=True and input is empty)

        Raises:
            click.BadParameter: If verses format is invalid
        """
        if value is None:
            value = ""

        normalized = value.strip()
        is_valid, payload = validate_verses(normalized, allow_empty=self.allow_empty)
        if is_valid:
            return payload
        self.fail(payload, param, ctx)
