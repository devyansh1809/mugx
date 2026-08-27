"""
Phase 4: Layer Editor - Interactive Canvas Widget
"""

from PyQt6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor, QCursor
import io


class SelectionHandle:
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4
    ROTATE = 5


class CanvasWidget(QGraphicsView):
    layer_transform_changed = pyqtSignal(str, float, float, float, float)
    layer_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None
        self.renderer = None
        self._current_layer_id = None
        self._selected_handle = SelectionHandle.NONE
        self._drag_start_pos = None
        self._is_dragging = False
        self._init_view()
    
    def _init_view(self):
        self.setRenderHint(QGraphicsView.RenderHint.Antialiasing)
        self.setRenderHint(QGraphicsView.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
    
    def set_engine(self, engine, renderer) -> None:
        self.engine = engine
        self.renderer = renderer
        self.refresh()
    
    def refresh(self) -> None:
        if not self.engine or not self.renderer: return
        self.scene.clear()
        image = self.renderer.render()
        data = io.BytesIO()
        image.save(data, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(data.getvalue(), "PNG")
        self.scene.addPixmap(pixmap)
        if self._current_layer_id: self._draw_selection_box()
    
    def _draw_selection_box(self) -> None:
        if not self.engine: return
        layer = self.engine.document.get_layer(self._current_layer_id)
        if not layer: return
        x, y = layer.transform.x, layer.transform.y
        width, height = 100 * layer.transform.scale, 100 * layer.transform.scale
        rect = QGraphicsRectItem(x, y, width, height)
        rect.setPen(QPen(QColor(0, 120, 215), 2))
        rect.setBrush(QBrush(QColor(0, 120, 215, 30)))
        self.scene.addItem(rect)
        rotate_handle_x, rotate_handle_y = x + width / 2, y - 20
        rotate_rect = QGraphicsRectItem(rotate_handle_x - 6, rotate_handle_y - 6, 12, 12)
        rotate_rect.setPen(QPen(QColor(0, 120, 215), 2))
        rotate_rect.setBrush(QBrush(QColor(255, 255, 255)))
        self.scene.addItem(rotate_rect)
    
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self._selected_handle = self._get_handle_at_pos(pos)
            if self._selected_handle != SelectionHandle.NONE:
                self._is_dragging = True
                self._drag_start_pos = pos
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event) -> None:
        pos = self.mapToScene(event.pos())
        handle = self._get_handle_at_pos(pos)
        if handle == SelectionHandle.TOP_LEFT or handle == SelectionHandle.BOTTOM_RIGHT: self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif handle == SelectionHandle.TOP_RIGHT or handle == SelectionHandle.BOTTOM_LEFT: self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        elif handle == SelectionHandle.ROTATE: self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else: self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        if self._is_dragging and self._selected_handle != SelectionHandle.NONE:
            if self._current_layer_id and self.engine: self._handle_drag(pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._selected_handle = SelectionHandle.NONE
        super().mouseReleaseEvent(event)
    
    def _get_handle_at_pos(self, pos: QPointF) -> int:
        if not self._current_layer_id or not self.engine: return SelectionHandle.NONE
        layer = self.engine.document.get_layer(self._current_layer_id)
        if not layer: return SelectionHandle.NONE
        x, y = layer.transform.x, layer.transform.y
        width, height = 100 * layer.transform.scale, 100 * layer.transform.scale
        handle_size = 12
        if abs(pos.x() - x) < handle_size and abs(pos.y() - y) < handle_size: return SelectionHandle.TOP_LEFT
        elif abs(pos.x() - (x + width)) < handle_size and abs(pos.y() - y) < handle_size: return SelectionHandle.TOP_RIGHT
        elif abs(pos.x() - x) < handle_size and abs(pos.y() - (y + height)) < handle_size: return SelectionHandle.BOTTOM_LEFT
        elif abs(pos.x() - (x + width)) < handle_size and abs(pos.y() - (y + height)) < handle_size: return SelectionHandle.BOTTOM_RIGHT
        rotate_x, rotate_y = x + width / 2, y - 20
        if abs(pos.x() - rotate_x) < handle_size and abs(pos.y() - rotate_y) < handle_size: return SelectionHandle.ROTATE
        return SelectionHandle.NONE
    
    def _handle_drag(self, pos: QPointF) -> None:
        if not self._current_layer_id or not self.engine: return
        layer = self.engine.document.get_layer(self._current_layer_id)
        if not layer: return
        dx, dy = pos.x() - self._drag_start_pos.x(), pos.y() - self._drag_start_pos.y()
        if self._selected_handle == SelectionHandle.TOP_LEFT:
            new_x, new_y = layer.transform.x + dx, layer.transform.y + dy
            self.engine.set_layer_position(self._current_layer_id, new_x, new_y)
        elif self._selected_handle == SelectionHandle.BOTTOM_RIGHT:
            scale_factor = 1.0 + (dx / 100.0)
            self.engine.scale_layer(self._current_layer_id, scale_factor)
        elif self._selected_handle == SelectionHandle.ROTATE:
            angle = dx * 2
            self.engine.rotate_layer(self._current_layer_id, angle)
        self._drag_start_pos = pos
        self.refresh()
        self.layer_transform_changed.emit(self._current_layer_id, layer.transform.x, layer.transform.y, layer.transform.scale, layer.transform.rotation)
    
    def select_layer(self, layer_id: str) -> None:
        self._current_layer_id = layer_id
        self.refresh()
        self.layer_selected.emit(layer_id)
    
    def clear_selection(self) -> None:
        self._current_layer_id = None
        self.refresh()
