"""
Tests for translation comparison bug fix.

Verifies that the save prompt is only shown when comparison data is successfully
fetched, preventing AttributeError when trying to save None data.
"""

import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock, call

from app.analytics.translation_compare import fetch_verse_comparison
from app.menus.analytics_menu import run_analytic_menu


class TestTranslationCompareBugFix:
    """Tests for translation comparison bug fix"""

    def test_no_save_prompt_when_fetch_fails(self, mocker: MockerFixture):
        """Test that save prompt is not shown when comparison fetch fails"""
        # Mock the menu choice to select translation comparison
        mock_prompt_menu = mocker.patch('app.menus.analytics_menu.prompt_menu_choice', return_value=2)
        
        # Mock user inputs
        mock_click_prompt = mocker.patch('app.menus.analytics_menu.click.prompt')
        mock_click_prompt.side_effect = ['John', '3', '16', '1', '2']  # book, chapter, verses, trans1, trans2
        
        # Mock input for translation selection and continue prompt
        mock_input = mocker.patch('builtins.input')
        mock_input.side_effect = ['1', '2', '']  # translation choices, then continue
        
        # Mock fetch_verse_comparison to return None (simulating failure)
        mock_fetch = mocker.patch('app.menus.analytics_menu.fetch_verse_comparison', return_value=None)
        
        # Mock console and other UI elements
        mock_console = mocker.patch('app.menus.analytics_menu.console')
        mock_render_book = mocker.patch('app.menus.analytics_menu.render_book_list')
        mocker.patch('app.menus.analytics_menu.spacing_after_output')
        
        # Mock the menu to return 0 to exit
        mock_prompt_menu.side_effect = [2, 0]
        
        try:
            # This should not crash even when fetch fails
            run_analytic_menu()
        except (AttributeError, KeyError) as e:
            pytest.fail(f"Function should not crash when fetch fails, but got: {e}")
        
        # Verify fetch was called
        assert mock_fetch.called
        
        # Verify that input was NOT called for save prompt (since data is None)
        # The input calls should only be for translation selection (2) and continue (1)
        # Check that none of the input calls contain "save" in the prompt text
        save_prompts = [args for args, _ in mock_input.call_args_list 
                       if args and len(args) > 0 and 'save' in str(args[0]).lower()]
        assert len(save_prompts) == 0, "Save prompt should not be shown when fetch fails"
        # Should have exactly 3 input calls: 2 for translation selection + 1 for continue
        assert len(mock_input.call_args_list) == 3, "Should have 3 input calls (2 translations + continue)"

    def test_save_prompt_shown_when_fetch_succeeds(self, mocker: MockerFixture):
        """Test that save prompt IS shown when comparison fetch succeeds"""
        # Mock the menu choice to select translation comparison
        mock_prompt_menu = mocker.patch('app.menus.analytics_menu.prompt_menu_choice', return_value=2)
        
        # Mock user inputs
        mock_click_prompt = mocker.patch('app.menus.analytics_menu.click.prompt')
        mock_click_prompt.side_effect = ['John', '3', '16']  # book, chapter, verses
        
        # Mock input for translation selection, save choice, and continue prompt
        mock_input = mocker.patch('builtins.input')
        mock_input.side_effect = ['1', '2', 'n', '']  # translation choices, then 'n' for save, then continue
        
        # Mock successful comparison data
        mock_comparison_data = {
            "reference": "John 3:16",
            "translation1": {
                "verses": [{"verse": 16, "text": "For God so loved..."}],
                "translation_name": "WEB",
                "translation_id": "web"
            },
            "translation2": {
                "verses": [{"verse": 16, "text": "For God so loved the world..."}],
                "translation_name": "KJV",
                "translation_id": "kjv"
            }
        }
        mock_fetch = mocker.patch('app.menus.analytics_menu.fetch_verse_comparison', 
                                 return_value=mock_comparison_data)
        
        # Mock console and other UI elements
        mock_console = mocker.patch('app.menus.analytics_menu.console')
        mock_render_book = mocker.patch('app.menus.analytics_menu.render_book_list')
        mock_render_comparison = mocker.patch('app.menus.analytics_menu.render_side_by_side_comparison')
        mocker.patch('app.menus.analytics_menu.spacing_after_output')
        
        # Mock calculate_translation_differences
        mocker.patch('app.menus.analytics_menu.calculate_translation_differences', return_value={})
        
        # Mock AnalysisTracker
        mock_tracker = Mock()
        mocker.patch('app.menus.analytics_menu.AnalysisTracker', return_value=mock_tracker)
        
        # Mock AppState
        mock_state = Mock()
        mock_state.current_user_id = "user123"
        mock_state.current_session_id = None
        mock_appstate = mocker.patch('app.menus.analytics_menu.AppState', return_value=mock_state)
        
        # Mock the menu to return 0 to exit
        mock_prompt_menu.side_effect = [2, 0]
        
        try:
            run_analytic_menu()
        except Exception as e:
            pytest.fail(f"Function should work when fetch succeeds, but got: {e}")
        
        # Verify fetch was called
        assert mock_fetch.called
        
        # Verify comparison was rendered
        mock_render_comparison.assert_called_once_with(mock_comparison_data)
        
        # Verify input was called for save prompt (should be in the calls)
        # Should have 4 input calls: 2 for translation selection + 1 for save + 1 for continue
        assert len(mock_input.call_args_list) == 4, "Should have 4 input calls (2 translations + save + continue)"
        # Check that one of the input calls contains "save" in the prompt text
        save_prompts = [args for args, _ in mock_input.call_args_list 
                       if args and len(args) > 0 and 'save' in str(args[0]).lower()]
        assert len(save_prompts) == 1, "Save prompt should be shown when fetch succeeds"

