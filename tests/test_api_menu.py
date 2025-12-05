import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock, MagicMock

from app.menus.api_menu import handle_fetch_by_ref, handle_save


class TestHandleFetchByRef:
    """Testit handle_fetch_by_ref-funktiolle"""

    def test_mode_v_successful_fetch(self, mocker: MockerFixture):
        """Testaa että mode 'v' hakee verse-tiedot onnistuneesti"""
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
        """Testaa että mode 'v' palauttaa None kun haku epäonnistuu"""
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
        """Testaa että mode 'c' hakee chapter-tiedot onnistuneesti"""
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
        """Testaa että mode 'c' palauttaa None kun haku epäonnistuu"""
        mock_prompt = mocker.patch('app.menus.api_menu.click.prompt')
        mock_prompt.side_effect = ['John', '3']
        
        mock_fetch = mocker.patch('app.menus.api_menu.fetch_by_reference')
        mock_fetch.return_value = None
        
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('c')
        
        assert result is None
        mock_fetch.assert_called_once_with('John', '3', None)
        mock_logger.error.assert_called_once_with("Failed to fetch verse. Check logs for details.")

    def test_mode_r_returns_none(self):
        """Testaa että mode 'r' palauttaa None"""
        result = handle_fetch_by_ref('r')
        assert result is None

    def test_invalid_mode(self, mocker: MockerFixture):
        """Testaa että virheellinen mode logittaa virheen ja palauttaa None"""
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        result = handle_fetch_by_ref('invalid')
        
        assert result is None
        mock_logger.error.assert_called_once_with("Invalid mode: invalid. Must be 'v', 'c', or 'r'")


class TestHandleSave:
    """Testit handle_save-funktiolle"""

    def test_save_success(self, mocker: MockerFixture):
        """Testaa että tallennus onnistuu kun käyttäjä valitsee tallentaa"""
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
        mock_logger.info.assert_called_once_with("Result saved successfully")

    def test_save_exception(self, mocker: MockerFixture):
        """Testaa että poikkeus käsitellään oikein tallennuksen aikana"""
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
        """Testaa että tallennusta ei tehdä kun käyttäjä kieltäytyy"""
        mock_confirm = mocker.patch('app.menus.api_menu.click.confirm')
        mock_confirm.return_value = False
        
        mock_querydb = mocker.patch('app.menus.api_menu.QueryDB')
        mock_logger = mocker.patch('app.menus.api_menu.logger')
        
        test_data = {'reference': 'John 3:16', 'verses': []}
        handle_save(test_data)
        
        mock_confirm.assert_called_once_with("Do you want to save result the result? [y/N] ", default=True)
        mock_querydb.assert_not_called()
        mock_logger.info.assert_called_once_with("Result not saved")
