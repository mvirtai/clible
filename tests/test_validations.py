import pytest
from app.validations.validations import (
    validate_books,
    validate_chapter,
    validate_verses,
    VERSES_MIN,
    VERSES_MAX,
    CHAPTERS_MIN,
    CHAPTER_MAX
)


class TestValidateBooks:
    """Testit validate_books-funktiolle"""
    
    @pytest.mark.parametrize("book_input,expected", [
        ("john", True),
        ("JOHN", True),
        ("John", True),
        ("  john  ", True),  # whitespace normalisointi
        ("1 john", True),
        ("2 samuel", True),
        ("psalms", True),
    ])
    def test_valid_books(self, book_input, expected):
        """Testaa että validit kirjat hyväksytään eri muodoissa"""
        result = validate_books(book_input)
        assert result == expected
    
    @pytest.mark.parametrize("invalid_book", [
        "joh",
        "john1",  # yhdistetty muoto
        "genesis1",
        "notabook",
        "",
        "123",
    ])
    def test_invalid_books(self, invalid_book):
        """Testaa että virheelliset kirjat hylätään"""
        result = validate_books(invalid_book)
        assert result is False


class TestValidateChapter:
    """Testit validate_chapter-funktiolle"""
    
    @pytest.mark.parametrize("chapter_input,expected_valid", [
        ("1", True),
        ("150", True),  # maksimi
        ("75", True),
        ("  42  ", True),  # whitespace
    ])
    def test_valid_chapters(self, chapter_input, expected_valid):
        """Testaa että validit luvut hyväksytään"""
        is_valid, payload = validate_chapter(chapter_input)
        assert is_valid == expected_valid
        if expected_valid:
            assert payload == chapter_input.strip()
    
    @pytest.mark.parametrize("invalid_chapter,expected_error", [
        ("0", f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}"),
        ("151", f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}"),
        ("-1", f"Chapter is either less than {CHAPTERS_MIN} or more than {CHAPTER_MAX}"),
        ("abc", "Chapter is not numeric value"),
        ("12.5", "Chapter is not numeric value"),
        ("", "Chapter is not numeric value"),
    ])
    def test_invalid_chapters(self, invalid_chapter, expected_error):
        """Testaa että virheelliset luvut hylätään oikealla virheilmoituksella"""
        is_valid, error_msg = validate_chapter(invalid_chapter)
        assert is_valid is False
        assert expected_error in error_msg


class TestValidateVerses:
    """Testit validate_verses-funktiolle"""
    
    @pytest.mark.parametrize("verses_input,expected_valid", [
        ("1", True),
        ("16", True),
        ("175", True),  # maksimi
        ("1-3", True),
        ("16-18", True),
        ("1-3,5", True),  # range + yksittäinen
        ("1,3,5", True),  # useita yksittäisiä
        ("16-18,20-22", True),  # useita rangeja
        ("  16  ", True),  # whitespace
        (" 16-18 ", True),  # whitespace range
    ])
    def test_valid_verses(self, verses_input, expected_valid):
        """Testaa että validit jaet hyväksytään"""
        is_valid, payload = validate_verses(verses_input)
        assert is_valid == expected_valid
        if expected_valid:
            assert payload == verses_input.strip()
    
    @pytest.mark.parametrize("invalid_verses,expected_error", [
        # Yksittäiset virheelliset
        ("0", f"Verse must be in range {VERSES_MIN} - {VERSES_MAX}"),
        ("176", f"Verse must be in range {VERSES_MIN} - {VERSES_MAX}"),
        ("abc", "Verse must be a number"),
        
        # Range-virheet
        ("11-1", "Start verse must be less than end verse"),  # tämä oli sun bugi!
        ("1-176", f"Verses must be in range {VERSES_MIN}-{VERSES_MAX}"),
        ("0-5", f"Verses must be in range {VERSES_MIN}-{VERSES_MAX}"),
        ("1-abc", "Verse numbers must be integers"),
        ("abc-5", "Verse numbers must be integers"),
        
        # Monimutkaiset virheet
        ("1-3,0", f"Verse must be in range {VERSES_MIN} - {VERSES_MAX}"),  # toinen osa virheellinen
        ("1-3,11-1", "Start verse must be less than end verse"),  # toinen range virheellinen
        
        # Muoto-virheet
        ("1-2-3", "Invalid verse range format, use 'start-end'"),  # liikaa viivoja
        ("-", "Invalid verse range format, use 'start-end'"),
        ("", "Verse must be a number"),
    ])
    def test_invalid_verses(self, invalid_verses, expected_error):
        """Testaa että virheelliset jaet hylätään oikealla virheilmoituksella"""
        is_valid, error_msg = validate_verses(invalid_verses)
        assert is_valid is False
        assert expected_error in error_msg