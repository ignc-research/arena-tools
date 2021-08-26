from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
from HelperFunctions import *

class KeyPressEater(QtCore.QObject):
    '''
    This class can be used to intercept all key presses happening in the application
    and then choose to handle it or relay it to the application.
    All Events will be passed to the given handleEventFunction.
    It should return True if the event was handled otherwise False
    '''
    def __init__(self, handleEventFunction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app = QtWidgets.QApplication.instance()  # get current application
        app.installEventFilter(self)
        self.handleEventFunction = handleEventFunction

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        return self.handleEventFunction(event)
        


class ArenaGraphicsPathItem(QtWidgets.QGraphicsPathItem):
    '''
    A QGraphicsPathItem that is connected to a QGraphicsScene and two QDoubleSpinBoxes
    that hold the position of this item.
    '''

    def __init__(self, parentWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parentWidget = parentWidget
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            )

        self.isDragged = False

        # create brush
        brush = QtGui.QBrush(QtGui.QColor("red"), QtCore.Qt.BrushStyle.SolidPattern)
        self.setBrush(brush)
        # create pen
        pen = QtGui.QPen()
        pen.setWidthF(0.01)
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        # add text item for displaying the name next to the item
        self.textItem = QtWidgets.QGraphicsTextItem("")
        self.textItem.setZValue(5)  # place text item above everything else
        self.textItem.setScale(0.035)
        parentWidget.graphicsScene.addItem(self.textItem)
        self.updateTextItemPos()

        # catch key presses for interacting with the item in the scene
        self.keyPressEater = KeyPressEater(self.handleEvent)
        
        self.oldItemPos = self.scenePos()

    # Alternative version of updateTextItemPos().
    # Calculate the bounding circle of the item and
    # place the text at an angle of 1/2 * PI.
    # def updateTextItemPos(self):
    #     # get radius of bounding circle
    #     rect = self.path().boundingRect()
    #     center = rect.center()
    #     point = rect.topLeft()
    #     diff = point - center
    #     radius = np.sqrt(diff.x() ** 2 + diff.y() ** 2)
    #     # get cartesian coordinates from polar coordinates
    #     x = np.cos((1/4) * 2 * np.pi) * radius
    #     y = np.sin((1/4) * 2 * np.pi) * radius
    #     # set text item pos
    #     pos = self.mapToScene(self.transformOriginPoint())
    #     pos += QtCore.QPointF(x, y)
    #     self.textItem.setPos(pos)

    def updateTextItemPos(self):
        pos = self.mapToScene(self.transformOriginPoint())
        # move a bit because the anchor position of text is top left
        pos += QtCore.QPointF(-0.3, -0.5)
        self.textItem.setPos(pos)

    def setPosNoEvent(self, x, y):
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        super().setPos(x, y)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.updateTextItemPos()
            self.parentWidget.handleItemChange()

        return super().itemChange(change, value)

    def mousePressEvent(self, mouse_event):
        for item in self.scene().selectedItems():
            item.isDragged = True
        self.isDragged = True

        self.oldMousePos = mouse_event.scenePos()
        self.oldItemPos = self.scenePos()
        # save positions for all items in scene
        for item in self.scene().items():
            if hasattr(item, "oldItemPos"):
                item.oldItemPos = item.scenePos()
        self.oldItemRotation = self.rotation()
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if modifier == QtCore.Qt.KeyboardModifier.ControlModifier:
            self.ctrlPressed = True
        else:
            self.ctrlPressed = False

        return super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        # rotate
        if self.isDragged and self.ctrlPressed:
            diff = mouse_event.scenePos() - self.oldMousePos
            angle = np.arctan2(diff.y(), diff.x())
            angle = 360 * angle / (2 * np.pi)  # convert radians to degrees
            self.setRotation(angle)
            self.updateTextItemPos()
        # translate
        elif self.isDragged:
            diff = mouse_event.scenePos() - self.oldMousePos
            for item in self.scene().selectedItems():
                if hasattr(item, "oldItemPos"):
                    item.setPos(item.oldItemPos + diff)

    def mouseReleaseEvent(self, mouse_event):
        for item in self.scene().selectedItems():
            if hasattr(item, "isDragged"):
                item.isDragged = False
        return super().mouseReleaseEvent(mouse_event)

    def mouseDoubleClickEvent(self, mouse_event):
        self.parentWidget.handleMouseDoubleClick()

    def handleEvent(self, event):
        # delete item when selected and DELETE key pressed
        if (event.type() == QtCore.QEvent.Type.KeyRelease
            and event.key() == QtCore.Qt.Key.Key_Delete
            and self.isSelected()):
            self.remove()

        # return false so event is not consumed and can be handled by other items aswell
        return False

    def remove(self):
        self.parentWidget.remove()



class ArenaGraphicsEllipseItem(QtWidgets.QGraphicsEllipseItem):
    '''
    A QGraphicsEllipseItem that is connected to two QDoubleSpinBoxes
    that hold the position of this item.
    '''

    def __init__(self, xSpinBox: QtWidgets.QDoubleSpinBox = None, ySpinBox: QtWidgets.QDoubleSpinBox = None, *args, handlePositionChangeMethod = None, **kwargs):
        """
        args:
            - xSpinBox: a spin box for the X-coordinate that shall be connected to this item
            - ySpinBox: a spin box for the Y-coordinate that shall be connected to this item
            - handlePositionChangeMethod: A method of the parent widget that should be called when this items position changes.
                It should take a QPointF as argument.
        """
        super().__init__(*args, **kwargs)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            )
        self.isDragged = False

        # set brush
        brush = QtGui.QBrush(QtGui.QColor("green"), QtCore.Qt.BrushStyle.SolidPattern)
        self.setBrush(brush)
        # set pen
        pen = QtGui.QPen()
        pen.setWidthF(0.01)
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        # text item for displaying the name next to the item, needs to be enabled by calling self.enableTextItem by parent
        self.textItem = QtWidgets.QGraphicsTextItem("")
        self.textItem.setScale(0.05)
        self.textItemEnabled = False

        self.xSpinBox = xSpinBox
        self.ySpinBox = ySpinBox

        self.handlePositionChangeMethod = handlePositionChangeMethod

        self.oldItemPos = self.scenePos()
        self.ctrlPressed = False

    def enableTextItem(self, scene: QtWidgets.QGraphicsScene, text: str):
        '''
        Add QGraphicsTextItem to scene and set its text.
        '''
        if not self.textItemEnabled:
            scene.addItem(self.textItem)
            self.textItem.setPlainText(text)
            self.textItemEnabled = True

    def updateTextItemPos(self):
        if self.textItemEnabled:
            self.textItem.setPos(self.scenePos())

    def setPosNoEvent(self, x, y):
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        super().setPos(x, y)
        self.updateTextItemPos()
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.handlePositionChangeMethod != None:
                self.handlePositionChangeMethod(self.scenePos())
            self.updateTextItemPos()
            if self.xSpinBox is not None and self.ySpinBox is not None:
                self.xSpinBox.setValue(self.pos().x())
                self.ySpinBox.setValue(self.pos().y())

        return super().itemChange(change, value)

    def mousePressEvent(self, mouse_event):
        for item in self.scene().selectedItems():
            item.isDragged = True
        self.isDragged = True

        self.oldMousePos = mouse_event.scenePos()
        self.oldItemPos = self.scenePos()
        # save positions for all items in scene
        for item in self.scene().items():
            if hasattr(item, "oldItemPos"):
                item.oldItemPos = item.scenePos()
        self.oldItemRotation = self.rotation()
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if modifier == QtCore.Qt.KeyboardModifier.ControlModifier:
            self.ctrlPressed = True
        else:
            self.ctrlPressed = False

        return super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        # rotate
        if self.isDragged and self.ctrlPressed:
            diff = mouse_event.scenePos() - self.oldMousePos
            angle = np.arctan2(diff.y(), diff.x())
            angle = 360 * angle / (2 * np.pi)  # convert radians to degrees
            self.setRotation(angle)
            self.updateTextItemPos()
        # translate
        elif self.isDragged:
            diff = mouse_event.scenePos() - self.oldMousePos
            for item in self.scene().selectedItems():
                if hasattr(item, "oldItemPos"):
                    item.setPos(item.oldItemPos + diff)

    def mouseReleaseEvent(self, mouse_event):
        for item in self.scene().selectedItems():
            if hasattr(item, "isDragged"):
                item.isDragged = False
        return super().mouseReleaseEvent(mouse_event)



class WaypointGraphicsEllipseItem(ArenaGraphicsEllipseItem):
    '''
    This item is meant to visualize a waypoint and is connected to a parent WaypointWidget.
    '''
    def __init__(self, waypointWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.waypointWidget = waypointWidget

        # set color
        brush = QtGui.QBrush(QtGui.QColor("blue"), QtCore.Qt.BrushStyle.SolidPattern)
        self.setBrush(brush)

        self.keyPressEater = KeyPressEater(self.handleEvent)

    def setPosNoEvent(self, x, y):
        super().setPosNoEvent(x, y)
        self.waypointWidget.pedsimAgentWidget.drawWaypointPath()

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.waypointWidget.updateSpinBoxesFromGraphicsItem()
            self.waypointWidget.pedsimAgentWidget.drawWaypointPath()

        return super().itemChange(change, value)

    def handleEvent(self, event):
        if (event.type() == QtCore.QEvent.Type.KeyRelease
            and event.key() == QtCore.Qt.Key.Key_Delete
            and self.isSelected()):
            self.remove()
            return True

        return False

    def remove(self):
        self.waypointWidget.remove()


class SubgoalEllipseItem(ArenaGraphicsEllipseItem):
    '''
    This item is meant to visualize a subgoal and is connected to a parent PathCreator.
    '''
    def __init__(self, pathCreator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pathCreator = pathCreator

        # set color
        brush = QtGui.QBrush(QtGui.QColor("blue"), QtCore.Qt.BrushStyle.SolidPattern)
        self.setBrush(brush)

        self.keyPressEater = KeyPressEater(self.handleEvent)

    def setPosNoEvent(self, x, y):
        super().setPosNoEvent(x, y)
        self.pathCreator.drawWaypointPath()

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.pathCreator.drawWaypointPath()

        return super().itemChange(change, value)

    def handleEvent(self, event):
        if (event.type() == QtCore.QEvent.Type.KeyRelease
            and event.key() == QtCore.Qt.Key.Key_Delete
            and self.isSelected()):
            self.remove()
            return True

        return False

    def remove(self):
        self.pathCreator.removeWaypoint(self)


class ArenaQGraphicsPolygonItem(QtWidgets.QGraphicsPolygonItem):
    '''
    A QGraphicsPolygonItem that is connected to a QGraphicsScene and two QDoubleSpinBoxes
    that hold the position of this item.
    Each vertice of the polygon can be moved by dragging.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            )
        self.setAcceptHoverEvents(True)
        self.footprint_widget = None
        # handles for resizing
        self.handle_size = 0.3  # length of one side of a rectangular handle
        self.handles = []  # list of QRectangle
        self.updateHandlesPos()
        self.point_index = -1

    def handleAt(self, point):
        """
        Returns the index of the resize handle below the given point.
        """
        valid_handles = []
        for i, handle in enumerate(self.handles):
            if handle.contains(point):
                valid_handles.append(i)

        # select handle which center is closest to *point*
        min_diff = float("inf")
        selected_handle_idx = -1
        for handle_idx in valid_handles:
            diff = point - self.handles[handle_idx].center()
            diff_len = np.linalg.norm([diff.x(), diff.y()])
            if diff_len < min_diff:
                min_diff = diff_len
                selected_handle_idx = handle_idx
                
        return selected_handle_idx

    def mousePressEvent(self, mouse_event):
        """
        Executed when the mouse is pressed on the item.
        """
        self.footprint_widget.dragging_polygon = True
        self.point_index = self.handleAt(mouse_event.pos())
        self.mouse_press_pos = mouse_event.pos()
        self.mouse_press_polygon = self.polygon()
        return super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.point_index != -1:
            # moving one vertice
            self.interactiveResize(self.point_index, mouse_event.pos())
        else:
            # moving the whole polygon
            for i in range(len(self.polygon())):
                self.interactiveResize(i, mouse_event.pos())

    def mouseReleaseEvent(self, mouse_event):
        """
        Executed when the mouse is released from the item.
        """
        self.footprint_widget.dragging_polygon = False
        self.point_index = -1
        self.mouse_press_pos = None
        self.mouse_press_polygon = None
        self.setPolygon(self.getRoundedPolygon())
        self.footprint_widget.update_spin_boxes()
        return super().mouseReleaseEvent(mouse_event)

    def interactiveResize(self, point_index_, mouse_pos):
        polygon = self.polygon()
        diff = mouse_pos - self.mouse_press_pos
        polygon[point_index_] = self.mouse_press_polygon[point_index_] + diff
        self.setPolygon(polygon)
        self.setPolygon(self.getRoundedPolygon())
        self.footprint_widget.update_spin_boxes()

    def setPolygon(self, *args):
        super().setPolygon(*args)
        self.updateHandlesPos()

    def updateHandlesPos(self):
        d = self.handle_size
        self.handles = []
        for point in self.polygon():
            rect = QtCore.QRectF(point.x() - d / 2.0, point.y() - d / 2.0, d, d)
            self.handles.append(rect)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.footprint_widget.update_spin_boxes()

        return super().itemChange(change, value)

    def getRoundedPolygon(self) -> QtGui.QPolygonF:
        mapped_polygon = self.mapToScene(self.polygon())
        for i in range(len(mapped_polygon)):
            mapped_polygon[i] = QtCore.QPointF(round_to_closest_20th(mapped_polygon[i].x()), round_to_closest_20th(mapped_polygon[i].y()))
        rounded_polygon = self.mapFromScene(mapped_polygon)
        return rounded_polygon

    def hoverMoveEvent(self, move_event):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        handle = self.handleAt(move_event.pos())
        if handle != -1:
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
        else:
            self.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)

        return super().hoverMoveEvent(move_event)



class ActiveModeWindow(QtWidgets.QMessageBox):
    '''
    A Window that pops up to indicate that a special mode has been activated.
    In this case it's the "Add Waypoints Mode".
    '''
    def __init__(self, connectedWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connectedWidget = connectedWidget
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.setWindowTitle("Add Waypoints...")
        self.setText("Click anywhere on the map to add a waypoint.\nPress ESC to finish.")
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        self.move(1000, 180)
        self.buttonClicked.connect(self.disable)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.disable()
        return super().keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.disable()
        return super().closeEvent(event)

    def disable(self):
        self.connectedWidget.addWaypointModeActive = False
        self.hide()



class Line(QtWidgets.QFrame):
    '''
    A simple line that can be added to a layout to separate widgets.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setMinimumWidth(300)
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)



class ArenaProbabilitySliderWidget(QtWidgets.QWidget):
    '''
    A Widget containing a slider and a percentage label.
    It has a logarithmic scale to give finer control for smaller probabilities.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 0.0
        self.values = np.array([0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        self.setup_ui()
        self.updateValueFromSlider()

    def setup_ui(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setMinimumWidth(300)

        # slider
        self.slider = QtWidgets.QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(19)
        self.slider.setValue(9)
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.slider.valueChanged.connect(self.updateValueFromSlider)
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.layout().addWidget(self.slider)

        # label
        self.label = QtWidgets.QLabel("")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.label.setMinimumWidth(50)
        self.layout().addWidget(self.label)

        # unit
        self.unitLabel = QtWidgets.QLabel("%")
        self.unitLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.unitLabel.setMinimumWidth(30)
        self.layout().addWidget(self.unitLabel)

    def updateValueFromSlider(self):
        new_value = self.values[self.slider.value()]
        self.value = new_value
        self.label.setText("{:4.2f}".format(new_value * 100))

    def setValue(self, value: float):
        # get absolute differences
        values = np.abs(self.values - value)
        min_idx = np.argmin(values)
        # set slider position
        # actual value and label will be updated by sliders valueChanged signal
        self.slider.setValue(min_idx)

    def getValue(self):
        return self.value



class ArenaSliderWidget(QtWidgets.QWidget):
    '''
    A Widget containing a slider and labels to display the value and a unit.
    '''
    def __init__(self, minValue: int, numValues: int, stepValue: float, unit: str = "", **kwargs):
        super().__init__(**kwargs)
        assert isinstance(minValue, int)
        assert isinstance(numValues, int)
        self.minValue = minValue
        self.numValues = numValues
        self.stepValue = stepValue
        self.unit = unit
        self.value = 0.0
        self.setup_ui()
        self.udpateValueFromSlider()

    def setup_ui(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setMinimumWidth(300)

        # slider
        self.slider = QtWidgets.QSlider()
        self.slider.setMinimum(self.minValue)
        self.slider.setMaximum(self.minValue + self.numValues)
        self.slider.setValue(self.minValue + (self.numValues // 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.slider.valueChanged.connect(self.udpateValueFromSlider)
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.layout().addWidget(self.slider)

        # label
        self.label = QtWidgets.QLabel("")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.label.setMinimumWidth(50)
        self.layout().addWidget(self.label)

        # unit
        self.unitLabel = QtWidgets.QLabel(self.unit)
        self.unitLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.unitLabel.setMinimumWidth(30)
        self.layout().addWidget(self.unitLabel)

    def udpateValueFromSlider(self):
        new_value = self.slider.value() * self.stepValue
        self.value = new_value
        self.label.setText("{:4.2f}".format(new_value))

    def setValue(self, value: float):
        # construct list of actual possible values for this slider
        values = (np.arange(self.numValues + 1) * self.stepValue) + self.minValue
        # get absolute differences
        abs_diffs = np.abs(values - value)
        min_idx = np.argmin(abs_diffs)
        # set slider position
        # actual value and label will be updated by sliders valueChanged signal
        self.slider.setValue(min_idx)

    def getValue(self):
        return self.value



class ArenaQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    '''
    A QDoubleSpinBox where a single step is 0.1 and the value will be rounded on every step up or down.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSingleStep(0.1)
        self.setMinimum(-100.0)
        self.setValue(0.0)

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.stepUp()
            event.accept()
        elif angle < 0:
            self.stepDown()
            event.accept()
        else:
            event.ignore()

    def stepUp(self):
        new_value = round(self.value() + self.singleStep(), 1)
        self.setValue(new_value)

    def stepDown(self):
        new_value = round(self.value() - self.singleStep(), 1)
        self.setValue(new_value)



class ArenaQGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def removeSelected(self):
        for item in self.selectedItems():
            if isinstance(item, ArenaGraphicsPathItem):
                item.remove()



class ArenaQGraphicsView(QtWidgets.QGraphicsView):
    '''
    A custom QGraphicsView.
    - can be dragged by mouse
    - can be zoomed by mouse wheel
    - sends mouse click positions (except clicks from dragging)
    '''
    clickedPos = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setSceneRect(-200, -200, 400, 400)
        self.zoomFactor = 1.0
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # add coordinate system lines
        pen = QtGui.QPen()
        pen.setWidthF(0.01)
        self.scene().addLine(0, -100, 0, 100, pen)
        self.scene().addLine(-100, 0, 100, 0, pen)

        # set initial view
        rect = QtCore.QRectF(-1.5, -1.5, 3, 3)
        self.fitInView(rect, mode=QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.lastMousePos = QtCore.QPointF()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.lastMousePos = event.pos()
        if event.buttons() & QtCore.Qt.MouseButton.RightButton:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)

        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # only emit signal if mouse was not dragged
        diff = event.pos() - self.lastMousePos
        diff_len = diff.x() + diff.y()
        if abs(diff_len) < 2.0:
            pos = self.mapToScene(event.pos())
            self.clickedPos.emit(pos)
        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """
        Zoom in or out of the view.
        """
        zoomInFactor = 1.25
        zoomOutFactor = 1 / zoomInFactor

        # Save the scene pos
        oldPos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor_ = zoomInFactor
        else:
            zoomFactor_ = zoomOutFactor
        self.scale(zoomFactor_, zoomFactor_)
        self.zoomFactor *= 1 / zoomFactor_

        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())
