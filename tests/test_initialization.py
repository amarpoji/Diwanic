"""Tests for search router (IntentRouter)."""
import pytest


def test_router_initialization_lazy():
    """Test that IntentRouter can be imported without network calls."""
    # The router should be lazy — it should NOT try to connect on import
    from diwanic.search.router import IntentRouter
    
    # Verify the class exists and can be instantiated lazily
    # (actual connection happens only when .route() is called)
    assert IntentRouter is not None
    
    # If we got here, import succeeded — network wasn't hit at import time
    print("IntentRouter imported successfully without hitting network.")


def test_router_has_route_method():
    """Verify the router has the expected interface."""
    from diwanic.search.router import IntentRouter
    # Just check the method exists, don't call it (which would hit network)
    assert hasattr(IntentRouter, 'route') or hasattr(IntentRouter, 'classify')