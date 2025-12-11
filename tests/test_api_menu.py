import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock, MagicMock

from app.menus.api_menu import handle_fetch_by_ref, handle_save


class TestHandleFetchByRef:
    """Tests for handle_fetch_by_ref function"""

    def test_mode_v_successful_fetch(self, mocker: MockerFixture):
        """Test that mode 'v' successfully fetches verse data"""
        mock_prompt = mocker.patch('app.menus.api_menu.click.prompt')
        mock_prompt.side_effect = ['John', '3', '16']
        
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        expected_data = {
            'reference': 'John 3:16',
            'verses': [{'book_name': 'John', 'chapter': 3, 'verse': 16, 'text': 'For God so loved...'}]
        }
        mock_fetch.return_value = expected_data
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('v')
        
        assert result == expected_data
        assert mock_prompt.call_count == 3
        mock_fetch.assert_called_once_with('John', '3', '16')
        mock_logger.info.assert_called_once_with("Fetched verse(s) successfully")

    def test_mode_v_failed_fetch(self, mocker: MockerFixture):
        """Test that mode 'v' returns None when fetch fails"""
        mock_prompt = mocker.patch('app.menus.api_menu.click.prompt')
        mock_prompt.side_effect = ['John', '3', '16']
        
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        mock_fetch.return_value = None
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('v')
        
        assert result is None
        mock_fetch.assert_called_once_with('John', '3', '16')
        mock_logger.error.assert_called_once_with("Failed to fetch verse. Check logs for details.")

    def test_mode_c_successful_fetch(self, mocker: MockerFixture):
        """Test that mode 'c' successfully fetches chapter data"""
        mock_prompt = mocker.patch('app.menus.api_menu.click.prompt')
        mock_prompt.side_effect = ['John', '3']
        
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        expected_data = {
            'reference': 'John 3',
            'verses': []
        }
        mock_fetch.return_value = expected_data
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('c')
        
        assert result == expected_data
        assert mock_prompt.call_count == 2
        mock_fetch.assert_called_once_with('John', '3', None)
        mock_logger.info.assert_called_once_with("Fetched chapter successfully")

    def test_mode_c_failed_fetch(self, mocker: MockerFixture):
        """Test that mode 'c' returns None when fetch fails"""
        mock_prompt = mocker.patch('app.menus.api_menu.click.prompt')
        mock_prompt.side_effect = ['John', '3']
        
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        mock_fetch.return_value = None
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('c')
        
        assert result is None
        mock_fetch.assert_called_once_with('John', '3', None)
        mock_logger.error.assert_called_once_with("Failed to fetch verse. Check logs for details.")
    
    def test_mode_r_successful_fetch(self, mocker: MockerFixture):
        """Test that mode 'r' successfully fetches random verse data"""
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        expected_data = {
            'reference': 'John 3:16',
            'verses': [{
                'book_id': 'JHN',
                'book_name': 'John',
                'chapter': 3,
                'verse': 16,
                'text': 'For God so loved...'
            }],
            'translation_id': 'web',
            'translation_name': 'World English Bible',
            'translation_note': 'Public Domain'
        }
        mock_fetch.return_value = expected_data
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('r')
        
        assert result == expected_data
        mock_fetch.assert_called_once_with(None, None, None, True)
        mock_logger.info.assert_called_once_with("Fetched random verse successfully")

    def test_mode_r_failed_fetch(self, mocker: MockerFixture):
        """Test that mode 'r' returns None when fetch fails"""
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        mock_fetch.return_value = None
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('r')
        
        assert result is None
        mock_fetch.assert_called_once_with(None, None, None, True)
        mock_logger.error.assert_called_once_with("Failed to fetch verse. Check logs for details.")

    def test_invalid_mode(self, mocker: MockerFixture):
        """Test that invalid mode logs error and returns None"""
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('invalid')
        
        assert result is None
        mock_logger.error.assert_called_once_with("Invalid mode: invalid. Must be 'v', 'c', or 'r'")


class TestHandleSave:
    """Tests for handle_save function"""

    def test_save_success(self, mocker: MockerFixture):
        """Test that save succeeds when user chooses to save"""
        mock_confirm = mocker.patch('app.menus.api_menu.click.confirm')
        mock_confirm.return_value = True
        
        mock_db = Mock()
        mock_db.save_query = Mock()
        
        mock_querydb = mocker.patch('app.menus.api_menu.QueryDB')
        mock_querydb.return_value.__enter__ = Mock(return_value=mock_db)
        mock_querydb.return_value.__exit__ = Mock(return_value=False)
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        test_data = {'reference': 'John 3:16', 'verses': []}
        handle_save(test_data)
        
        mock_confirm.assert_called_once_with("Do you want to save result the result? [y/N] ", default=True)
        mock_db.save_query.assert_called_once_with(test_data)
        mock_logger.info.assert_called_once_with("Result saved successfully (id=%s)", mock_db.save_query.return_value)

    def test_save_exception(self, mocker: MockerFixture):
        """Test that exception is handled correctly during save"""
        mock_confirm = mocker.patch('app.menus.api_menu.click.confirm')
        mock_confirm.return_value = True
        
        mock_db = Mock()
        test_exception = Exception("Database error")
        mock_db.save_query.side_effect = test_exception
        
        mock_querydb = mocker.patch('app.menus.api_menu.QueryDB')
        mock_querydb.return_value.__enter__ = Mock(return_value=mock_db)
        mock_querydb.return_value.__exit__ = Mock(return_value=False)
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        test_data = {'reference': 'John 3:16', 'verses': []}
        handle_save(test_data)
        
        mock_db.save_query.assert_called_once_with(test_data)
        mock_logger.error.assert_called_once_with(f"Failed to save result: {test_exception}")
        mock_logger.info.assert_not_called()

    def test_save_declined(self, mocker: MockerFixture):
        """Test that save is not performed when user declines"""
        mock_confirm = mocker.patch('app.menus.api_menu.click.confirm')
        mock_confirm.return_value = False
        
        mock_querydb = mocker.patch('app.menus.api_menu.QueryDB')
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        test_data = {'reference': 'John 3:16', 'verses': []}
        handle_save(test_data)
        
        mock_confirm.assert_called_once_with("Do you want to save result the result? [y/N] ", default=True)
        mock_querydb.assert_not_called()
        mock_logger.info.assert_called_once_with("Result not saved")
