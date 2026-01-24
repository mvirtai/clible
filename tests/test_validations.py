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
        ("150", True),
        ("75", True),
        ("  42  ", True),
        ("all", True),
        ("ALL", True),
        ("  all  ", True),
    ])
    def test_valid_chapters(self, chapter_input, expected_valid):
        """Testaa että validit luvut hyväksytään"""
        is_valid, payload = validate_chapter(chapter_input)
        assert is_valid == expected_valid
        if expected_valid:
            if chapter_input.strip().lower() == "all":
                assert payload == "all"
            else:
                assert payload == chapter_input.strip()
    
    @pytest.mark.parametrize("invalid_chapter,expected_error", [
        ("0", f"Chapter must be between {CHAPTERS_MIN} and {CHAPTER_MAX}"),
        ("151", f"Chapter must be between {CHAPTERS_MIN} and {CHAPTER_MAX}"),
        ("-1", "Chapter must be a numeric value"),
        ("abc", "Chapter must be a numeric value"),
        ("12.5", "Chapter must be a numeric value"),
        ("", "Chapter cannot be empty"),
    ])
    def test_invalid_chapters(self, invalid_chapter, expected_error):
        """Testaa että virheelliset luvut hylätään oikealla virheilmoituksella"""
        is_valid, error_msg = validate_chapter(invalid_chapter)
        assert is_valid is False
        assert expected_error in error_msg
    
    def test_chapter_all_keyword(self):
        """Test that 'all' keyword is accepted when allow_all=True"""
        is_valid, payload = validate_chapter("all", allow_all=True)
        assert is_valid is True
        assert payload == "all"
        
        # Test that 'all' is rejected when allow_all=False
        is_valid, payload = validate_chapter("all", allow_all=False)
        assert is_valid is False
        assert "cannot be 'all'" in payload


class TestValidateVerses:
    """Testit validate_verses-funktiolle"""
    
    @pytest.mark.parametrize("verses_input,expected_valid", [
        ("1", True),
        ("16", True),
        ("175", True), 
        ("1-3", True),
        ("16-18", True),
        ("1-3,5", True),  
        ("1,3,5", True),  
        ("16-18,20-22", True), 
        ("  16  ", True),  
        (" 16-18 ", True),  
    ])
    def test_valid_verses(self, verses_input, expected_valid):
        """Testaa että validit jaet hyväksytään"""
        is_valid, payload = validate_verses(verses_input)
        assert is_valid == expected_valid
        if expected_valid:
            assert payload == verses_input.strip()
    
    @pytest.mark.parametrize("invalid_verses,expected_error", [
        # Single invalid inputs
        ("0", f"Verse must be between {VERSES_MIN} and {VERSES_MAX}"),
        ("176", f"Verse must be between {VERSES_MIN} and {VERSES_MAX}"),
        ("abc", "Verse must be a number"),
        # Range errors
        ("11-1", "Start verse must be less than or equal to end verse"),
        ("1-176", f"End verse must be between {VERSES_MIN} and {VERSES_MAX}"),
        ("0-5", f"Start verse must be between {VERSES_MIN} and {VERSES_MAX}"),
        ("1-abc", "Verse numbers must be integers"),
        ("abc-5", "Verse numbers must be integers"),
        # Complex errors
        ("1-3,0", f"Verse must be between {VERSES_MIN} and {VERSES_MAX}"),
        ("1-3,11-1", "Start verse must be less than or equal to end verse"),
        # Format errors
        ("1-2-3", "Invalid verse range format"),
        ("-", "Invalid verse range format"),
        ("", "Verse cannot be empty"),
    ])
    def test_invalid_verses(self, invalid_verses, expected_error):
        """Testaa että virheelliset jaet hylätään oikealla virheilmoituksella"""
        is_valid, error_msg = validate_verses(invalid_verses)
        assert is_valid is False
        assert expected_error in error_msg