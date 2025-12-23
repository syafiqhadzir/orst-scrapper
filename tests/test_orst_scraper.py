import pytest
from unittest.mock import Mock, patch
from scripts.orst_scraper import ORSTScraper
from scripts.api_client import APIResponse

class TestORSTScraper:
    
    @pytest.fixture
    def scraper(self, mock_config):
        with patch('scripts.orst_scraper.ORSTAPIClient') as mock_client_cls:
            scraper = ORSTScraper(mock_config, resume=False)
            scraper.client = mock_client_cls.return_value
            yield scraper

    def test_scrape_character_success(self, scraper):
        """Test scraping a single character."""
        scraper.client.fetch_all_pages.return_value = ["คำ", "คำคม"]
        
        words = scraper.scrape_character("ค")
        
        assert len(words) == 2
        assert "คำ" in words
        scraper.client.fetch_all_pages.assert_called_once_with("ค")
        
    def test_process_words(self, scraper):
        """Test word processing (deduplication, sorting, filtering)."""
        raw_words = ["ก", "ข", "ก", "a", " "] # specific mix
        
        # Depending on config in mock_config fixture:
        # validate_thai_only=True -> 'a' removed
        # normalize_unicode=True -> done in scrape step usually, but check here if calls utils
        
        processed = scraper.process_words(raw_words)
        
        assert "a" not in processed # English removed
        assert processed.count("ก") == 1 # Deduplicated
        assert processed == ["ก", "ข"] # Sorted Thai order
