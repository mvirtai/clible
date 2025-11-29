import click
<<<<<<< HEAD
<<<<<<< HEAD
from app.validations.validations import validate_books, validate_chapter, validate_verses
=======
from app.validations.validations import validate_books, validate_chapter
>>>>>>> 79ce083 (Refactor CLI input handling to use custom parameter types for book and chapter validation)
=======
from app.validations.validations import validate_books, validate_chapter, validate_verses
>>>>>>> f407d63 (Enhanced CLI logic by adding custom click.Types for parameters. Added validations for those parameters and added tests for those validation functions.)


class BookParam(click.ParamType):
   name = "book"

   def convert(self, value, param, ctx):
        normalized = value.strip().lower()
        if validate_books(normalized):
            return normalized.title()
        self.fail(f"Unknown book: {value}", param, ctx)


class ChapterParam(click.ParamType):
    name = "chapter"

    def convert(self, value, param, ctx):
        normalized = value.strip()
        is_valid, payload = validate_chapter(normalized)
        if is_valid:
            return payload
        self.fail(payload, param, ctx)
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> f407d63 (Enhanced CLI logic by adding custom click.Types for parameters. Added validations for those parameters and added tests for those validation functions.)


class VersesParam(click.ParamType):
    name = "verses"

    def convert(self, value, param, ctx):
        normalized = value.strip()
        is_valid, payload = validate_verses(normalized)
        if is_valid:
            return payload
        self.fail(payload, param, ctx)

<<<<<<< HEAD
=======
>>>>>>> 79ce083 (Refactor CLI input handling to use custom parameter types for book and chapter validation)
=======
>>>>>>> f407d63 (Enhanced CLI logic by adding custom click.Types for parameters. Added validations for those parameters and added tests for those validation functions.)
