import pytest
from unittest.mock import MagicMock
from diwanic.embeddings.generator import PoemEmbedder

def test_embedder_initialization(monkeypatch):
    """Test that embedder loads the correct model from config."""
    mock_st = MagicMock()
    monkeypatch.setattr("diwanic.embeddings.generator.SentenceTransformer", lambda x: mock_st)
    
    embedder = PoemEmbedder(model_name="test-model")
    assert embedder.model_name == "test-model"

def test_embed_empty_text(monkeypatch):
    """Test that embedding empty text returns a zero vector."""
    mock_st = MagicMock()
    mock_st.get_embedding_dimension.return_value = 384
    monkeypatch.setattr("diwanic.embeddings.generator.SentenceTransformer", lambda x: mock_st)
    
    embedder = PoemEmbedder()
    vec = embedder.embed_text("")
    assert len(vec) == 384
    assert all(v == 0.0 for v in vec)
