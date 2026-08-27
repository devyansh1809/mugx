"""
Phase 4: Layer Editor - Layer Engine with Undo/Redo
"""

from typing import List, Optional, Any, Callable
from dataclasses import dataclass
import copy


@dataclass
class Command:
    name: str
    execute: Callable[[], None]
    undo: Callable[[], None]


class LayerEngine:
    def __init__(self, document: Any):
        self.document = document
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_undo_steps: int = 50
        self._suppress_undo: bool = False
    
    def _add_undo(self, command: Command) -> None:
        if not self._suppress_undo:
            self.undo_stack.append(command)
            self.redo_stack.clear()
            if len(self.undo_stack) > self.max_undo_steps: self.undo_stack.pop(0)
    
    def undo(self) -> bool:
        if not self.undo_stack: return False
        command = self.undo_stack.pop()
        self._suppress_undo = True
        try: command.undo()
        finally: self._suppress_undo = False
        self.redo_stack.append(command)
        return True
    
    def redo(self) -> bool:
        if not self.redo_stack: return False
        command = self.redo_stack.pop()
        self._suppress_undo = True
        try: command.execute()
        finally: self._suppress_undo = False
        self.undo_stack.append(command)
        return True
    
    def can_undo(self) -> bool: return len(self.undo_stack) > 0
    def can_redo(self) -> bool: return len(self.redo_stack) > 0
    def clear_history(self) -> None: self.undo_stack.clear(); self.redo_stack.clear()
    
    def add_layer(self, layer: Any, index: Optional[int] = None) -> None:
        old_layers = copy.deepcopy(self.document.layers)
        old_active = self.document.active_layer_id
        self.document.add_layer(layer, index)
        def undo_add(): self.document.layers = old_layers; self.document.active_layer_id = old_active
        def redo_add(): self.document.add_layer(layer, index)
        self._add_undo(Command(name="add_layer", execute=redo_add, undo=undo_add))
    
    def remove_layer(self, layer_id: str) -> Optional[Any]:
        layer = self.document.get_layer(layer_id)
        if not layer: return None
        old_layers = copy.deepcopy(self.document.layers)
        old_active = self.document.active_layer_id
        self.document.remove_layer(layer_id)
        def undo_remove(): self.document.layers = old_layers; self.document.active_layer_id = old_active
        def redo_remove(): self.document.remove_layer(layer_id)
        self._add_undo(Command(name="remove_layer", execute=redo_remove, undo=undo_remove))
        return layer
    
    def duplicate_layer(self, layer_id: str) -> Optional[Any]:
        import uuid
        layer = self.document.get_layer(layer_id)
        if not layer: return None
        new_layer = copy.deepcopy(layer)
        new_layer.id = str(uuid.uuid4())
        current_index = None
        for i, l in enumerate(self.document.layers):
            if l.id == layer_id: current_index = i; break
        new_index = current_index + 1 if current_index is not None else None
        self.add_layer(new_layer, new_index)
        return new_layer
    
    def move_layer(self, layer_id: str, dx: float, dy: float) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_x, old_y = layer.transform.x, layer.transform.y
        layer.transform.x += dx; layer.transform.y += dy
        def undo_move(): layer.transform.x = old_x; layer.transform.y = old_y
        def redo_move(): layer.transform.x += dx; layer.transform.y += dy
        self._add_undo(Command(name="move_layer", execute=redo_move, undo=undo_move))
        return True
    
    def set_layer_position(self, layer_id: str, x: float, y: float) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_x, old_y = layer.transform.x, layer.transform.y
        layer.transform.x = x; layer.transform.y = y
        def undo_set(): layer.transform.x = old_x; layer.transform.y = old_y
        def redo_set(): layer.transform.x = x; layer.transform.y = y
        self._add_undo(Command(name="set_position", execute=redo_set, undo=undo_set))
        return True
    
    def scale_layer(self, layer_id: str, factor: float) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_scale = layer.transform.scale
        layer.transform.scale *= factor
        def undo_scale(): layer.transform.scale = old_scale
        def redo_scale(): layer.transform.scale *= factor
        self._add_undo(Command(name="scale_layer", execute=redo_scale, undo=undo_scale))
        return True
    
    def rotate_layer(self, layer_id: str, angle: float) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_rotation = layer.transform.rotation
        layer.transform.rotation += angle
        def undo_rotate(): layer.transform.rotation = old_rotation
        def redo_rotate(): layer.transform.rotation += angle
        self._add_undo(Command(name="rotate_layer", execute=redo_rotate, undo=undo_rotate))
        return True
    
    def bring_to_front(self, layer_id: str) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_index = self.document.layers.index(layer)
        self.document.move_layer(layer_id, len(self.document.layers) - 1)
        def undo_bring(): self.document.move_layer(layer_id, old_index)
        def redo_bring(): self.document.move_layer(layer_id, len(self.document.layers) - 1)
        self._add_undo(Command(name="bring_to_front", execute=redo_bring, undo=undo_bring))
        return True
    
    def send_to_back(self, layer_id: str) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_index = self.document.layers.index(layer)
        self.document.move_layer(layer_id, 0)
        def undo_send(): self.document.move_layer(layer_id, old_index)
        def redo_send(): self.document.move_layer(layer_id, 0)
        self._add_undo(Command(name="send_to_back", execute=redo_send, undo=undo_send))
        return True
    
    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_visible = layer.properties.visible
        layer.properties.visible = visible
        def undo_vis(): layer.properties.visible = old_visible
        def redo_vis(): layer.properties.visible = visible
        self._add_undo(Command(name="set_visibility", execute=redo_vis, undo=undo_vis))
        return True
    
    def set_layer_opacity(self, layer_id: str, opacity: float) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        old_opacity = layer.properties.opacity
        layer.properties.opacity = max(0.0, min(1.0, opacity))
        def undo_op(): layer.properties.opacity = old_opacity
        def redo_op(): layer.properties.opacity = max(0.0, min(1.0, opacity))
        self._add_undo(Command(name="set_opacity", execute=redo_op, undo=undo_op))
        return True
    
    def set_active_layer(self, layer_id: str) -> bool:
        layer = self.document.get_layer(layer_id)
        if not layer: return False
        self.document.active_layer_id = layer_id
        return True
    
    def get_selected_layer(self) -> Optional[Any]:
        if not self.document.active_layer_id: return None
        return self.document.get_layer(self.document.active_layer_id)
    
    def get_layers_in_order(self) -> List[Any]: return self.document.layers.copy()
    def get_layer_count(self) -> int: return len(self.document.layers)
