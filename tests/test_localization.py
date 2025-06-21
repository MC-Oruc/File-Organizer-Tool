"""
Tests for localization.py functionality.
"""
import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from localization import LocaleManager


class TestLocaleManager:
    """Test the LocaleManager class."""
    
    @pytest.mark.unit
    def test_locale_manager_initialization(self):
        """Test LocaleManager initialization."""
        lm = LocaleManager()
        assert lm.default_lang == "en"
        assert lm.current_lang is not None
        assert isinstance(lm.available_languages, dict)
    
    @pytest.mark.unit
    def test_get_string_existing_key(self, mock_locale_manager):
        """Test getting an existing translation string."""
        result = mock_locale_manager.get_string("error_title")
        assert result == "Error"
    
    @pytest.mark.unit
    def test_get_string_nonexistent_key(self, mock_locale_manager):
        """Test getting a non-existent translation string."""
        result = mock_locale_manager.get_string("nonexistent_key")
        assert result == "nonexistent_key"  # Should return key if not found
    
    @pytest.mark.unit
    def test_get_string_with_formatting(self, mock_locale_manager):
        """Test getting a string with format parameters."""
        result = mock_locale_manager.get_string("export_tree_success", file="test.txt")
        assert "test.txt" in result
    
    @pytest.mark.unit
    def test_get_current_language_code(self, mock_locale_manager):
        """Test getting current language code."""
        assert mock_locale_manager.get_current_language_code() == "en"
    
    @pytest.mark.unit
    def test_set_language_valid(self):
        """Test setting a valid language."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock locale file
            locales_dir = os.path.join(temp_dir, "locales")
            os.makedirs(locales_dir)
            
            test_locale = {
                "_lang_name_": "Test Language",
                "test_key": "Test Value"
            }
            
            with open(os.path.join(locales_dir, "test.json"), 'w') as f:
                json.dump(test_locale, f)
            
            lm = LocaleManager(locales_dir=locales_dir, default_lang="test")
            lm.set_language("test")
            
            assert lm.current_lang == "test"
            assert lm.get_string("test_key") == "Test Value"
    
    @pytest.mark.unit
    def test_set_language_invalid(self):
        """Test setting an invalid language."""
        with tempfile.TemporaryDirectory() as temp_dir:
            locales_dir = os.path.join(temp_dir, "locales")
            os.makedirs(locales_dir)
            
            # Create only English locale
            en_locale = {"_lang_name_": "English", "test_key": "Test Value"}
            with open(os.path.join(locales_dir, "en.json"), 'w') as f:
                json.dump(en_locale, f)
            
            lm = LocaleManager(locales_dir=locales_dir, default_lang="en")
            lm.set_language("invalid_lang")
            
            # Should fall back to default
            assert lm.current_lang == "en"
    
    @pytest.mark.unit
    def test_load_available_languages(self):
        """Test loading available languages from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            locales_dir = os.path.join(temp_dir, "locales")
            os.makedirs(locales_dir)
            
            # Create multiple locale files
            locales = {
                "en": {"_lang_name_": "English"},
                "tr": {"_lang_name_": "Türkçe"},
                "de": {"_lang_name_": "Deutsch"}
            }
            
            for lang_code, content in locales.items():
                with open(os.path.join(locales_dir, f"{lang_code}.json"), 'w') as f:
                    json.dump(content, f)
            
            lm = LocaleManager(locales_dir=locales_dir)
            available = lm.get_available_languages_display()
            
            assert "en" in available
            assert "tr" in available
            assert "de" in available
            assert available["en"] == "English"
            assert available["tr"] == "Türkçe"
    
    @pytest.mark.unit
    def test_load_language_file_not_found(self):
        """Test loading a language file that doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            locales_dir = os.path.join(temp_dir, "locales")
            os.makedirs(locales_dir)
            
            lm = LocaleManager(locales_dir=locales_dir, default_lang="en")
            lm.load_language("nonexistent")
            
            # Should have empty translations
            assert lm.translations == {}
    
    @pytest.mark.unit
    def test_load_language_invalid_json(self):
        """Test loading a language file with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            locales_dir = os.path.join(temp_dir, "locales")
            os.makedirs(locales_dir)
            
            # Create file with invalid JSON
            with open(os.path.join(locales_dir, "invalid.json"), 'w') as f:
                f.write("{ invalid json")
            
            lm = LocaleManager(locales_dir=locales_dir, default_lang="en")
            lm.load_language("invalid")
            
            # Should have empty translations
            assert lm.translations == {}
    
    @pytest.mark.unit
    @patch('locale.getdefaultlocale')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_system_language_locale_module(self, mock_getdefaultlocale):
        """Test system language detection using locale module."""
        mock_getdefaultlocale.return_value = ('en_US', 'UTF-8')
        
        lm = LocaleManager()
        system_lang = lm.get_system_language()
        
        assert system_lang == "en"
    
    @pytest.mark.unit
    @patch('locale.getdefaultlocale')
    @patch.dict(os.environ, {'LANG': 'tr_TR.UTF-8'})
    def test_get_system_language_env_var(self, mock_getdefaultlocale):
        """Test system language detection using environment variable."""
        mock_getdefaultlocale.return_value = (None, None)
        
        lm = LocaleManager()
        system_lang = lm.get_system_language()
        
        assert system_lang == "tr"
    
    @pytest.mark.unit
    @patch('locale.getdefaultlocale')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_system_language_fallback(self, mock_getdefaultlocale):
        """Test system language detection fallback."""
        mock_getdefaultlocale.side_effect = Exception("Test error")
        
        lm = LocaleManager()
        system_lang = lm.get_system_language()
        
        assert system_lang == "en"  # Should fall back to default
    
    @pytest.mark.unit
    def test_format_string_missing_parameter(self, mock_locale_manager):
        """Test formatting string with missing parameter."""
        # This should not raise an exception but return unformatted string
        result = mock_locale_manager.get_string("export_tree_success")  # Missing 'file' parameter
        assert "export_tree_success" in result or "{file}" in result


class TestLocaleFiles:
    """Test actual locale files for consistency."""
    
    @pytest.mark.unit
    def test_all_locale_files_exist(self):
        """Test that all expected locale files exist."""
        expected_locales = ['en', 'de', 'es', 'fr', 'it', 'ja', 'pt', 'ru', 'tr', 'zh_CN']
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        for locale_code in expected_locales:
            locale_file = os.path.join(locales_dir, f"{locale_code}.json")
            assert os.path.exists(locale_file), f"Locale file {locale_code}.json not found"
    
    @pytest.mark.unit
    def test_locale_files_valid_json(self):
        """Test that all locale files contain valid JSON."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(locales_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON in {filename}")
    
    @pytest.mark.unit
    def test_locale_files_have_lang_name(self):
        """Test that all locale files have _lang_name_ key."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(locales_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    assert "_lang_name_" in data, f"Missing _lang_name_ in {filename}"
                    assert data["_lang_name_"], f"Empty _lang_name_ in {filename}"
    
    @pytest.mark.unit
    def test_locale_files_key_consistency(self):
        """Test that all locale files have the same keys."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        # Load English as reference
        en_file = os.path.join(locales_dir, 'en.json')
        with open(en_file, 'r', encoding='utf-8') as f:
            en_keys = set(json.load(f).keys())
        
        # Check other locale files
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json') and filename != 'en.json':
                file_path = os.path.join(locales_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_keys = set(data.keys())
                    
                    missing_keys = en_keys - file_keys
                    extra_keys = file_keys - en_keys
                    
                    assert not missing_keys, f"Missing keys in {filename}: {missing_keys}"
                    assert not extra_keys, f"Extra keys in {filename}: {extra_keys}"
    
    @pytest.mark.unit
    def test_locale_files_no_empty_values(self):
        """Test that locale files don't have empty string values."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(locales_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        assert value.strip(), f"Empty value for key '{key}' in {filename}"


@pytest.mark.integration
class TestLocalizationIntegration:
    """Integration tests for localization functionality."""
    
    def test_locale_manager_with_real_files(self):
        """Test LocaleManager with actual locale files."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        lm = LocaleManager(locales_dir=locales_dir)
        
        # Test loading different languages
        for lang_code in ['en', 'tr', 'de', 'fr']:
            lm.set_language(lang_code)
            assert lm.current_lang == lang_code
            
            # Test some common strings
            assert lm.get_string("window_title")
            assert lm.get_string("export_tree_button")
            assert lm.get_string("error_title")
    
    def test_string_formatting_with_real_locales(self):
        """Test string formatting with actual locale strings."""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        lm = LocaleManager(locales_dir=locales_dir)
        
        lm.set_language('en')
        result = lm.get_string("export_tree_success", file="test.txt")
        assert "test.txt" in result
        
        result = lm.get_string("status_preview_generated", category_count=5, file_count=25)
        assert "5" in result
        assert "25" in result 