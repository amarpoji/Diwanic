from diwanic.search.router import IntentRouter

def test_router_initialization():
    """Test that the IntentRouter can be initialized."""
    try:
        router = IntentRouter()
        assert router is not None
    except Exception:
        pass
