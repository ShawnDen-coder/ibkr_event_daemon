"""
Tests for the event bridge between eventkit and blinker.
"""

import pytest
from eventkit import Event
from blinker import signal
from demo.event_bridge import EventBridge

def test_event_bridge_patch():
    """Test that patching works correctly."""
    # Setup
    EventBridge.patch()
    
    # Verify patch is applied
    assert EventBridge._is_patched
    assert Event.__call__ != EventBridge._original_call

def test_event_bridge_unpatch():
    """Test that unpatching restores original behavior."""
    # Setup
    EventBridge.patch()
    original_call = EventBridge._original_call
    
    # Action
    EventBridge.unpatch()
    
    # Verify
    assert not EventBridge._is_patched
    assert Event.__call__ == original_call

def test_event_bridge_double_patch():
    """Test that double patching doesn't cause issues."""
    # First patch
    EventBridge.patch()
    
    # Second patch shouldn't change anything
    EventBridge.patch()
    
    # Verify still patched correctly
    assert EventBridge._is_patched
    assert Event.__call__ != EventBridge._original_call

def test_event_bridge_functionality():
    """Test that events are properly bridged to blinker signals."""
    # Setup
    EventBridge.patch()
    test_event = Event('test_event')
    received_data = []
    
    # Create blinker signal handler
    @signal('test_event').connect
    def handler(sender, *args, **kwargs):
        received_data.append((args, kwargs))
    
    # Create eventkit handler
    event_data = []
    def event_handler(*args, **kwargs):
        event_data.append((args, kwargs))
    test_event += event_handler
    
    # Trigger event
    test_args = (1, 2, 3)
    test_kwargs = {'a': 'b'}
    test_event(*test_args, **test_kwargs)
    
    # Verify both handlers received the data
    assert len(received_data) == 1
    assert len(event_data) == 1
    assert received_data[0][0] == test_args
    assert received_data[0][1] == test_kwargs
    assert event_data[0][0] == test_args
    assert event_data[0][1] == test_kwargs

def test_event_bridge_error_handling():
    """Test that errors in blinker handlers don't affect eventkit handlers."""
    # Setup
    EventBridge.patch()
    test_event = Event('error_test')
    event_handled = False
    
    # Create eventkit handler
    def event_handler():
        nonlocal event_handled
        event_handled = True
    test_event += event_handler
    
    # Create failing blinker handler
    @signal('error_test').connect
    def failing_handler(sender):
        raise Exception("Test error")
    
    # Trigger event
    test_event()
    
    # Verify eventkit handler still executed
    assert event_handled

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test."""
    yield
    # Restore original event behavior
    EventBridge.unpatch()
