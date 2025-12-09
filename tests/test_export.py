import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from pytest_mock import MockerFixture

from app.export import format_verse_data_markdown, export_query_to_markdown, EXPORT_DIR


class TestFormatVerseDataMarkdown:
    """Testit format_verse_data_markdown-funktiolle"""

    def test_format_with_all_fields(self):
        """Testaa että kaikki kentät formatoidaan oikein"""
        data = {
            'reference': 'John 3:16',
            'translation_name': 'King James Version',
            'translation_id': 'KJV',
            'translation_note': 'Authorized Version',
            'created_at': '2024-01-01 12:00:00',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'For God so loved the world...'}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '**Translation:** King James Version KJV' in result
        assert '*Authorized Version*' in result
        assert '**Saved**: 2024-01-01 12:00:00' in result
        assert '## Chapter 3' in result
        assert '**16** For God so loved the world...' in result

    def test_format_with_minimal_fields(self):
        """Testaa että minimikentät riittävät"""
        data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'For God so loved the world...'}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '## Chapter 3' in result
        assert '**16** For God so loved the world...' in result
        # Translation info käyttää oletusarvoa jos sitä ei ole
        assert '**Translation:** Unknown translation' in result

    def test_format_multiple_chapters(self):
        """Testaa että useampi luku formatoidaan oikein"""
        data = {
            'reference': 'John 3:16-4:2',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Verse 16 text'},
                {'chapter': 3, 'verse': 17, 'text': 'Verse 17 text'},
                {'chapter': 4, 'verse': 1, 'text': 'Verse 1 text'},
                {'chapter': 4, 'verse': 2, 'text': 'Verse 2 text'},
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        # Tarkista että molemmat luvut ovat olemassa
        assert '## Chapter 3' in result
        assert '## Chapter 4' in result
        # Tarkista että kaikki jaet ovat mukana
        assert '**16** Verse 16 text' in result
        assert '**17** Verse 17 text' in result
        assert '**1** Verse 1 text' in result
        assert '**2** Verse 2 text' in result
        # Tarkista että luvut erotetaan tyhjällä rivillä
        assert result.count('## Chapter') == 2

    def test_format_empty_verses(self):
        """Testaa että tyhjä jae-lista toimii"""
        data = {
            'reference': 'John 3:16',
            'verses': []
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '## Chapter' not in result
        assert '---' in result  # Separator pitäisi olla

    def test_format_missing_optional_fields(self):
        """Testaa että puuttuvat valinnaiset kentät eivät aiheuta virheitä"""
        data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        
        # Ei translation_note, translation_id, created_at
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '**16** Text' in result

    def test_format_unknown_reference(self):
        """Testaa että tuntematon viite käyttää oletusarvoa"""
        data = {
            'verses': [
                {'chapter': 1, 'verse': 1, 'text': 'Text'}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# Unknown reference' in result

    def test_format_verse_text_stripping(self):
        """Testaa että jae-tekstin whitespace käsitellään oikein"""
        data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': '  Text with spaces  '}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        # Teksti pitäisi olla trimmatty
        assert '**16** Text with spaces' in result
        assert '  Text with spaces  ' not in result


class TestExportQueryToMarkdown:
    """Testit export_query_to_markdown-funktiolle"""

    def test_export_success_with_auto_filename(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että export onnistuu automaattisella tiedostonimellä"""
        # Mock QueryDB
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'For God so loved the world...'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        # Mock EXPORT_DIR to use tmp_path
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        assert result.exists()
        assert result.name == 'John_3-16.md'
        assert result.parent == tmp_path / 'exports'
        
        # Tarkista tiedoston sisältö
        content = result.read_text(encoding='utf-8')
        assert '# John 3:16' in content
        assert '**16** For God so loved the world...' in content

    def test_export_success_with_custom_filename(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että export onnistuu mukautetulla tiedostonimellä"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        custom_path = Path('custom_export.md')
        result = export_query_to_markdown('test-query-id', custom_path)
        
        assert result is not None
        assert result.exists()
        assert result.name == 'custom_export.md'
        assert result.parent == tmp_path / 'exports'

    def test_export_success_with_absolute_path(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että absoluuttinen polku käytetään sellaisenaan"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        absolute_path = tmp_path / 'absolute_export.md'
        result = export_query_to_markdown('test-query-id', absolute_path)
        
        assert result is not None
        assert result.exists()
        assert result == absolute_path

    def test_export_query_not_found(self, mocker: MockerFixture):
        """Testaa että puuttuva query palauttaa None"""
        mock_db = Mock()
        mock_db.get_single_saved_query.return_value = None
        
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('non-existent-id')
        
        assert result is None

    def test_export_file_write_error(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että tiedostokirjoitusvirhe käsitellään oikein"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        # Mock open to raise an exception
        mocker.patch('builtins.open', side_effect=IOError("Permission denied"))
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is None

    def test_export_creates_export_directory(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että export-kansio luodaan automaattisesti jos sitä ei ole"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        export_dir = tmp_path / 'new_exports'
        mocker.patch('app.export.EXPORT_DIR', export_dir)
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        # Varmista että kansiota ei ole vielä
        assert not export_dir.exists()
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        assert export_dir.exists()
        assert export_dir.is_dir()

    def test_export_filename_special_characters(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että erikoismerkit korvataan tiedostonimessä"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16-18',  # Sisältää välilyönnin ja kaksoispisteen
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        # Välilyönnit korvataan alaviivoilla, kaksoispisteet viivoilla
        assert 'John_3-16-18.md' in str(result) or result.name == 'John_3-16-18.md'

    def test_export_with_translation_info(self, mocker: MockerFixture, tmp_path: Path):
        """Testaa että käännöstiedot sisällytetään exporttiin"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16',
            'translation_name': 'King James Version',
            'translation_id': 'KJV',
            'translation_note': 'Authorized Version',
            'created_at': '2024-01-01 12:00:00',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        content = result.read_text(encoding='utf-8')
        assert '**Translation:** King James Version KJV' in content
        assert '*Authorized Version*' in content
        assert '**Saved**: 2024-01-01 12:00:00' in content
