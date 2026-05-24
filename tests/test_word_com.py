import pytest
from unittest.mock import patch, MagicMock
from src.word_com import WordApp


def test_word_app_context_manager():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        with WordApp(visible=False) as app:
            assert app.app is not None

        mock_word.Quit.assert_called_once()


def test_apply_style():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        app = WordApp(visible=False)
        app.app = mock_word

        mock_selection = MagicMock()
        mock_word.Selection = mock_selection
        mock_style = MagicMock()
        mock_word.ActiveDocument.Styles.return_value = mock_style

        app.apply_style("heading_1")

        assert mock_selection.Style == mock_style


def test_insert_page_break():
    with patch("src.word_com.client.Dispatch") as mock_dispatch:
        mock_word = MagicMock()
        mock_dispatch.return_value = mock_word

        app = WordApp(visible=False)
        app.app = mock_word

        mock_selection = MagicMock()
        mock_word.Selection = mock_selection

        app.insert_page_break()

        mock_selection.InsertBreak.assert_called_once()
