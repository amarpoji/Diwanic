"""Tests for the Diwanic repository CRUD operations (mocked DB)."""
import pytest
from unittest.mock import MagicMock, patch
from diwanic.storage.repository import DiwanicRepository


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    return MagicMock()


@pytest.fixture
def repo(mock_session):
    """Create a DiwanicRepository with a mock session."""
    return DiwanicRepository(mock_session)


# ── Poet Tests ────────────────────────────────────────────────────

class TestPoetOperations:
    def test_get_poet_by_slug_found(self, repo, mock_session):
        mock_poet = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poet
        result = repo.get_poet_by_slug("Mutanabi")
        assert result == mock_poet

    def test_get_poet_by_slug_not_found(self, repo, mock_session):
        mock_session.query.return_value.filter.return_value.first.return_value = None
        result = repo.get_poet_by_slug("unknown-poet")
        assert result is None

    def test_create_poet(self, repo, mock_session):
        result = repo.create_poet(slug="test-slug", name_ar="شاعر تجريبي", era="العصر الحديث")
        assert result.slug == "test-slug"
        assert result.name_ar == "شاعر تجريبي"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_poet_by_id(self, repo, mock_session):
        mock_poet = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poet
        result = repo.get_poet_by_id("123")
        assert result == mock_poet


# ── Poem Tests ────────────────────────────────────────────────────

class TestPoemOperations:
    def test_get_poem_by_source_url_found(self, repo, mock_session):
        mock_poem = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poem
        result = repo.get_poem_by_source_url("https://aldiwan.net/poem1.html")
        assert result == mock_poem

    def test_create_poem(self, repo, mock_session):
        result = repo.create_poem(
            poet_id="poet-uuid-123",
            title="قصيدة تجريبية",
            original_text="أول سطر\nثاني سطر",
            searchable_text="اول سطر\nثاني سطر",
            source_url="https://aldiwan.net/poem1.html",
        )
        assert result.title == "قصيدة تجريبية"
        assert result.poet_id == "poet-uuid-123"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_poem_by_id(self, repo, mock_session):
        mock_poem = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_poem
        result = repo.get_poem_by_id("poem-uuid")
        assert result == mock_poem


# ── Verse Tests ───────────────────────────────────────────────────

class TestVerseOperations:
    def test_create_verses(self, repo, mock_session):
        verses = ["سطر أول", "سطر ثاني", "سطر ثالث"]
        searchable = ["اول سطر", "ثاني سطر", "ثالث سطر"]
        result = repo.create_verses(poem_id="poem-uuid", verses=verses, searchable_verses=searchable)
        assert len(result) == 3
        assert result[0].original_text == "سطر أول"
        assert result[1].verse_index == 1
        assert result[2].verse_index == 2
        assert mock_session.add.call_count == 3

    def test_create_verses_empty(self, repo, mock_session):
        result = repo.create_verses(poem_id="poem-uuid", verses=[], searchable_verses=[])
        assert result == []

    def test_get_verses_by_poem_id(self, repo, mock_session):
        mock_verses = [MagicMock(), MagicMock()]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_verses
        result = repo.get_verses_by_poem_id("poem-uuid")
        assert len(result) == 2

    def test_get_verses_by_poem_id_empty(self, repo, mock_session):
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = repo.get_verses_by_poem_id("nonexistent")
        assert result == []


# ── Search Tests ──────────────────────────────────────────────────

class TestSearch:
    def test_search_poems_by_keyword(self, repo, mock_session):
        mock_poems = [MagicMock(), MagicMock()]
        mock_session.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_poems
        result = repo.search_poems_by_keyword("حب", limit=5)
        assert len(result) == 2

    def test_search_poems_by_keyword_no_results(self, repo, mock_session):
        mock_session.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        result = repo.search_poems_by_keyword("xyz不存在")
        assert result == []
