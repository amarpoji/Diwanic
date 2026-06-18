"""Tests for search router (IntentRouter)."""
import pytest
import sys


def test_router_initialization_lazy():
    """Test that IntentRouter can be imported without network calls."""
    # Mock logfire before import to prevent any network telemetry
    mock_logfire = type('MockLogfire', (), {
        'configure': lambda self, **kw: None,
        'instrument_openai': lambda self, *a, **kw: None
    })()
    monkeypatch_dict = {'logfire': mock_logfire}
    
    for key in ['logfire', 'diwanic.search.router', 'diwanic.schemas.query']:
        if key in sys.modules:
            del sys.modules[key]
    
    # Patch logfire in sys.modules before importing router
    sys.modules['logfire'] = mock_logfire
    
    try:
        from diwanic.search.router import IntentRouter
        assert IntentRouter is not None
        print("IntentRouter imported successfully without hitting network.")
    finally:
        # Cleanup
        for key in ['logfire', 'diwanic.search.router', 'diwanic.schemas.query']:
            if key in sys.modules:
                del sys.modules[key]


def test_router_has_route_method():
    """Verify the router has the expected interface."""
    # Mock logfire before import to prevent any network telemetry
    mock_logfire = type('MockLogfire', (), {
        'configure': lambda self, **kw: None,
        'instrument_openai': lambda self, *a, **kw: None
    })()
    
    for key in ['logfire', 'diwanic.search.router', 'diwanic.schemas.query']:
        if key in sys.modules:
            del sys.modules[key]
    
    sys.modules['logfire'] = mock_logfire
    
    try:
        from diwanic.search.router import IntentRouter
        assert hasattr(IntentRouter, 'route') or hasattr(IntentRouter, 'classify')
    finally:
        for key in ['logfire', 'diwanic.search.router', 'diwanic.schemas.query']:
            if key in sys.modules:
                del sys.modules[key]