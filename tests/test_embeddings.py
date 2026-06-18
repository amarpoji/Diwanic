"""Tests for embeddings module."""
import pytest
import sys
import importlib


def test_embedder_initialization(monkeypatch):
    """Test that PoemEmbedder stores the model name correctly."""
    # Prevent real SentenceTransformer from loading
    mock_st_class = lambda name=None, **kw: type('MockModel', (), {
        'get_embedding_dimension': lambda self: 384
    })()
    monkeypatch.setitem(sys.modules, 'sentence_transformers', type('FakeModule', (), {'SentenceTransformer': mock_st_class}))
    
    if 'diwanic.embeddings.generator' in sys.modules:
        del sys.modules['diwanic.embeddings.generator']
    
    from diwanic.embeddings.generator import PoemEmbedder
    embedder = PoemEmbedder(model_name="test-model")
    assert embedder.model_name == "test-model"


def test_embed_empty_text(monkeypatch):
    """Test that embedding empty text returns a zero vector."""
    mock_st_class = lambda name=None, **kw: type('MockModel', (), {
        'get_embedding_dimension': lambda self: 384,
        'encode': lambda self, text, **kw: [0.0] * 384
    })()
    monkeypatch.setitem(sys.modules, 'sentence_transformers', type('FakeModule', (), {'SentenceTransformer': mock_st_class}))
    
    if 'diwanic.embeddings.generator' in sys.modules:
        del sys.modules['diwanic.embeddings.generator']
    
    from diwanic.embeddings.generator import PoemEmbedder
    embedder = PoemEmbedder(model_name="test-model")
    vec = embedder.embed_text("")
    assert len(vec) == 384
    assert all(v == 0.0 for v in vec)