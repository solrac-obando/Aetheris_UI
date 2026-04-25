import pytest
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel
from core.pooling import ElementPool
from core.lifecycle import get_lifecycle_manager

def test_full_system_integration():
    """Verify Engine, Pooling, Gestures and Lifecycle work together."""
    engine = AetherEngine()
    pool = ElementPool()
    lm = get_lifecycle_manager()
    
    # 1. Start with clean state
    lm.reset()
    assert lm.get_tracked_count() == 0
    
    # 2. Acquire elements from pool and register in engine
    for i in range(10):
        # Even indices: StaticBox, Odd: SmartPanel
        if i % 2 == 0:
            elem = pool.acquire(StaticBox, x=i*10, y=10, w=50, h=50)
        else:
            elem = pool.acquire(SmartPanel, x=0, y=0, w=100, h=100)
        engine.register_element(elem)
        
    assert engine.element_count == 10
    assert lm.get_tracked_count() == 10
    
    # 3. Simulate multiple ticks with viewport change
    engine.tick(800, 600)
    engine.tick(1024, 768)
    
    # 4. Simulate Gestures during tick
    engine.handle_pointer_down(5, 5, pointer_id=0) # Should hit first element
    engine.handle_pointer_move(10, 10, pointer_id=0)
    
    # Second pointer for pinch
    engine.handle_pointer_down(100, 100, pointer_id=1)
    engine.handle_pointer_move(150, 150, pointer_id=1)
    
    # Tick again to process physics with gestures
    data = engine.tick(1024, 768)
    assert len(data) == 10
    assert engine.input_manager.current_scale != 1.0
    
    # 5. Clean up
    engine.handle_pointer_up(0)
    engine.handle_pointer_up(1)
    
    # Dispose all via manager
    lm.dispose_all()
    assert lm.get_tracked_count() == 0
    
    # Final check: can we re-acquire after disposal?
    # elements are pooled even after dispose if we release them
    # Actually lm.dispose_all() calls element.dispose()
    # Let's check if pooling still works
    new_elem = pool.acquire(StaticBox, 0,0,10,10)
    assert new_elem.tensor is not None
    assert not new_elem.is_disposed
