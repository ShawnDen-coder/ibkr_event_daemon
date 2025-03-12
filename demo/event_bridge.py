"""
Event bridge between eventkit and blinker.
This module provides functionality to bridge eventkit events to blinker signals.
"""

from typing import Any, Optional, Dict
from eventkit import Event
from blinker import signal
import functools
import logging

logger = logging.getLogger(__name__)

class EventBridge:
    """Bridge between eventkit Events and blinker signals."""
    
    _original_call = Event.__call__
    _is_patched = False
    
    @classmethod
    def patch(cls) -> None:
        """
        Patch eventkit.Event to bridge all events to blinker signals.
        This should be called before any events are created.
        """
        if cls._is_patched:
            logger.warning("EventBridge is already patched")
            return
            
        @functools.wraps(cls._original_call)
        def patched_call(self: Event, *args: Any, **kwargs: Any) -> Any:
            # First call original event handler
            result = cls._original_call(self, *args, **kwargs)
            
            try:
                # Get or create corresponding blinker signal
                blink_signal = signal(self.name)
                
                # Send signal with the same args
                blink_signal.send(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in blinker bridge for event {self.name}: {e}")
                
            return result
            
        Event.__call__ = patched_call
        cls._is_patched = True
        logger.info("EventBridge patch applied")
    
    @classmethod
    def unpatch(cls) -> None:
        """
        Restore original eventkit.Event behavior.
        Useful for testing or cleanup.
        """
        if not cls._is_patched:
            logger.warning("EventBridge is not patched")
            return
            
        Event.__call__ = cls._original_call
        cls._is_patched = False
        logger.info("EventBridge patch removed")
    
    @staticmethod
    def get_signal(event_name: str):
        """
        Get blinker signal corresponding to an event name.
        
        Args:
            event_name: Name of the event
            
        Returns:
            blinker.Signal: The corresponding signal
        """
        return signal(event_name)
