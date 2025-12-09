import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from pytest_mock import MockerFixture

from app.export import format_verse_data_markdown, export_query_to_markdown, EXPORT_DIR


class TestFormatVerseDataMarkdown:
    """Tests for format_verse_data_markdown function"""

    def test_format_with_all_fields(self):
        """Test that all fields are formatted correctly"""
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
        """Test that minimal fields are sufficient"""
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
        # Translation info uses default value if not provided
        assert '**Translation:** Unknown translation' in result

    def test_format_multiple_chapters(self):
        """Test that multiple chapters are formatted correctly"""
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
        
        # Verify that both chapters exist
        assert '## Chapter 3' in result
        assert '## Chapter 4' in result
        # Verify that all verses are included
        assert '**16** Verse 16 text' in result
        assert '**17** Verse 17 text' in result
        assert '**1** Verse 1 text' in result
        assert '**2** Verse 2 text' in result
        # Verify that chapters are separated by blank line
        assert result.count('## Chapter') == 2

    def test_format_empty_verses(self):
        """Test that empty verse list works"""
        data = {
            'reference': 'John 3:16',
            'verses': []
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '## Chapter' not in result
        assert '---' in result  # Separator should be present

    def test_format_missing_optional_fields(self):
        """Test that missing optional fields don't cause errors"""
        data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        
        # No translation_note, translation_id, created_at
        result = format_verse_data_markdown(data)
        
        assert '# John 3:16' in result
        assert '**16** Text' in result

    def test_format_unknown_reference(self):
        """Test that unknown reference uses default value"""
        data = {
            'verses': [
                {'chapter': 1, 'verse': 1, 'text': 'Text'}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        assert '# Unknown reference' in result

    def test_format_verse_text_stripping(self):
        """Test that verse text whitespace is handled correctly"""
        data = {
            'reference': 'John 3:16',
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': '  Text with spaces  '}
            ]
        }
        
        result = format_verse_data_markdown(data)
        
        # Text should be trimmed
        assert '**16** Text with spaces' in result
        assert '  Text with spaces  ' not in result


class TestExportQueryToMarkdown:
    """Tests for export_query_to_markdown function"""

    def test_export_success_with_auto_filename(self, mocker: MockerFixture, tmp_path: Path):
        """Test that export succeeds with auto-generated filename"""
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
        
        # Verify file contents
        content = result.read_text(encoding='utf-8')
        assert '# John 3:16' in content
        assert '**16** For God so loved the world...' in content

    def test_export_success_with_custom_filename(self, mocker: MockerFixture, tmp_path: Path):
        """Test that export succeeds with custom filename"""
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
        """Test that absolute path is used as-is"""
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
        """Test that missing query returns None"""
        mock_db = Mock()
        mock_db.get_single_saved_query.return_value = None
        
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('non-existent-id')
        
        assert result is None

    def test_export_file_write_error(self, mocker: MockerFixture, tmp_path: Path):
        """Test that file write error is handled correctly"""
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
        """Test that export directory is created automatically if it doesn't exist"""
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
        
        # Verify that directory doesn't exist yet
        assert not export_dir.exists()
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        assert export_dir.exists()
        assert export_dir.is_dir()

    def test_export_filename_special_characters(self, mocker: MockerFixture, tmp_path: Path):
        """Test that special characters are replaced in filename"""
        mock_db = Mock()
        mock_data = {
            'reference': 'John 3:16-18',  # Contains space and colon
            'verses': [
                {'chapter': 3, 'verse': 16, 'text': 'Text'}
            ]
        }
        mock_db.get_single_saved_query.return_value = mock_data
        
        mocker.patch('app.export.EXPORT_DIR', tmp_path / 'exports')
        mocker.patch('app.export.QueryDB', return_value=mock_db)
        
        result = export_query_to_markdown('test-query-id')
        
        assert result is not None
        # Spaces replaced with underscores, colons with dashes
        assert 'John_3-16-18.md' in str(result) or result.name == 'John_3-16-18.md'

    def test_export_with_translation_info(self, mocker: MockerFixture, tmp_path: Path):
        """Test that translation info is included in export"""
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
