import pathlib
from PyQt5 import QtGui, QtCore, QtWidgets
import os
import time
import copy
from typing import Tuple, List
from FlatlandBodyEditor import *
from PedsimAgentEditor import *
from ArenaScenario import *
from QtExtensions import *
from HelperFunctions import *

class RosMapData():
    def __init__(self, path: str = ""):
        self.image_path = ""
        self.resolution = 1.0
        self.origin = [0.0, 0.0, 0.0]
        self.path = path
        if path != "":
            self.load(path)

    def load(self, path: str):
        if os.path.exists(path):
            self.path = path
            with open(path, "r") as file:
                data = yaml.safe_load(file)
                folder_path = os.path.dirname(path)
                self.image_path = os.path.join(folder_path, data["image"])
                self.resolution = float(data["resolution"])
                self.origin = [float(value) for value in data["origin"]]



class WaypointWidget(QtWidgets.QWidget):
    def __init__(self, pedsimAgentWidget, graphicsScene: QtWidgets.QGraphicsScene, posIn: QtCore.QPointF = None, **kwargs):
        super().__init__(**kwargs)
        self.id = 0
        self.pedsimAgentWidget = pedsimAgentWidget  # needed so the ellipse item can trigger a waypoint path redraw
        # create circle and add to scene
        self.ellipseItem = WaypointGraphicsEllipseItem(self, None, None, -0.25, -0.25, 0.5, 0.5)
        self.graphicsScene = graphicsScene
        graphicsScene.addItem(self.ellipseItem)
        # setup widgets
        self.setupUI()
        self.setId(self.id)
        # set initial position
        if posIn != None:
            self.setPos(posIn)

    def setupUI(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)

        # x value
        ## label
        label = QtWidgets.QLabel("x")
        self.layout().addWidget(label)
        ## spinbox
        self.posXSpinBox = ArenaQDoubleSpinBox()
        self.posXSpinBox.valueChanged.connect(self.updateEllipseItemFromSpinBoxes)
        self.layout().addWidget(self.posXSpinBox)

        # y value
        ## label
        label = QtWidgets.QLabel("y")
        self.layout().addWidget(label)
        ## spinbox
        self.posYSpinBox = ArenaQDoubleSpinBox()
        self.posYSpinBox.valueChanged.connect(self.updateEllipseItemFromSpinBoxes)
        self.layout().addWidget(self.posYSpinBox)

        # delete button
        delete_button = QtWidgets.QPushButton("X")
        delete_button.setFixedWidth(30)
        delete_button.setStyleSheet("background-color: red")
        delete_button.clicked.connect(self.remove)
        self.layout().addWidget(delete_button)

    def setId(self, id: int):
        self.id = id

    def setPos(self, posIn: QtCore.QPointF):
        # set values of spin boxes (and ellipse item)
        # since spin boxes are connected to the ellipse item, the change will be propagated
        self.posXSpinBox.setValue(posIn.x())
        self.posYSpinBox.setValue(posIn.y())

    def getPos(self) -> Tuple[float, float]:
        return self.posXSpinBox.value(), self.posYSpinBox.value()

    def updateEllipseItemFromSpinBoxes(self):
        if not self.ellipseItem.isDragged:  # do this to prevent recursion between spin boxes and graphics item
            x = self.posXSpinBox.value()
            y = self.posYSpinBox.value()
            self.ellipseItem.setPosNoEvent(x, y)  # set without event to prevent recursion between spin boxes and graphics item

    def updateSpinBoxesFromGraphicsItem(self):
        new_pos = self.ellipseItem.mapToScene(self.ellipseItem.transformOriginPoint())
        self.posXSpinBox.setValue(new_pos.x())
        self.posYSpinBox.setValue(new_pos.y())

    def remove(self):
        self.ellipseItem.scene().removeItem(self.ellipseItem)
        del self.ellipseItem.keyPressEater  # delete to remove event filter

        self.parent().layout().removeWidget(self)
        self.pedsimAgentWidget.updateWaypointIdLabels()
        self.pedsimAgentWidget.drawWaypointPath()
        self.deleteLater()



class PedsimAgentWidget(QtWidgets.QFrame):
    '''
    This is a row in the obstacles frame.
    '''
    def __init__(self, id: int, pedsimAgentIn: PedsimAgent, graphicsScene: QtWidgets.QGraphicsScene, graphicsView: ArenaQGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.graphicsScene = graphicsScene
        self.graphicsView = graphicsView
        self.pedsimAgent = pedsimAgentIn

        # create path item
        self.graphicsPathItem = ArenaGraphicsPathItem(self)
        # add to scene
        self.graphicsScene.addItem(self.graphicsPathItem)
        # setup widgets
        self.setup_ui()
        # setup pedsim agent editor
        self.pedsimAgentEditor = PedsimAgentEditor(self, parent=self.parent(), flags=QtCore.Qt.WindowType.Window)
        self.pedsimAgentEditor.editorSaved.connect(self.handleEditorSaved)

        # setup waypoints
        self.addWaypointModeActive = False
        self.activeModeWindow = ActiveModeWindow(self)
        graphicsView.clickedPos.connect(self.handleGraphicsViewClick)
        # GraphicsItem for drawing a path connecting the waypoints
        self.waypointPathItem = QtWidgets.QGraphicsPathItem()
        ## create brush
        brush = QtGui.QBrush(QtGui.QColor(), QtCore.Qt.BrushStyle.NoBrush)
        self.waypointPathItem.setBrush(brush)
        ## create pen
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor("lightseagreen"))
        pen.setWidthF(0.1)
        pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        self.waypointPathItem.setPen(pen)
        ## add to scene
        graphicsScene.addItem(self.waypointPathItem)

        self.updateEverythingFromPedsimAgent()

    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)

        # name label
        self.name_label = QtWidgets.QLabel(self.pedsimAgent.name)
        self.layout().addWidget(self.name_label, 0, 0)

        # edit button
        self.edit_button = QtWidgets.QPushButton("Edit")
        self.edit_button.clicked.connect(self.onEditClicked)
        self.layout().addWidget(self.edit_button, 0, 1)

        # delete button
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(self.onDeleteClicked)
        self.layout().addWidget(self.delete_button, 0, 2)

        # position
        label = QtWidgets.QLabel("Pos:")
        self.layout().addWidget(label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.posXSpinBox = ArenaQDoubleSpinBox()
        self.posXSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posXSpinBox, 1, 1)
        self.posYSpinBox = ArenaQDoubleSpinBox()
        self.posYSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posYSpinBox, 1, 2)

        # waypoints
        label = QtWidgets.QLabel("Waypoints:")
        self.layout().addWidget(label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        button = QtWidgets.QPushButton("Add Waypoints...")
        button.clicked.connect(self.onAddWaypointClicked)
        self.layout().addWidget(button, 2, 1, 1, -1)
        self.waypointListWidget = QtWidgets.QWidget()
        self.waypointListWidget.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.waypointListWidget, 3, 0, 1, -1)

    def handleMouseDoubleClick(self):
        # function will be called by the graphics item
        self.onEditClicked()

    def handleItemChange(self):
        # function will be called by the graphics item
        self.updateSpinBoxesFromGraphicsItem()
        self.drawWaypointPath()

    def drawWaypointPath(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.getCurrentAgentPosition())
        for w in self.getWaypointWidgets():
            w_pos = w.ellipseItem.mapToScene(w.ellipseItem.transformOriginPoint())
            path.lineTo(w_pos)

        self.waypointPathItem.setPath(path)

    def getCurrentAgentPosition(self):
        x = self.posXSpinBox.value()
        y = self.posYSpinBox.value()
        return QtCore.QPointF(x, y)

    def getWaypointWidgets(self):
        widgets = []
        for i in range(self.waypointListWidget.layout().count()):
            w = self.waypointListWidget.layout().itemAt(i).widget()
            if w != None:
                widgets.append(w)
        return widgets

    def updateSpinBoxesFromGraphicsItem(self):
        new_pos = self.graphicsPathItem.mapToScene(self.graphicsPathItem.transformOriginPoint())
        self.posXSpinBox.setValue(new_pos.x())
        self.posYSpinBox.setValue(new_pos.y())

    def updateGraphicsPathItemFromSpinBoxes(self):
        if not self.graphicsPathItem.isDragged:  # prevents recursive loop (spin box <-> moving item)
            x = self.posXSpinBox.value()
            y = self.posYSpinBox.value()
            self.graphicsPathItem.setPosNoEvent(x, y)
            self.drawWaypointPath()
            self.graphicsPathItem.updateTextItemPos()

    def updateGraphicsPathItemFromPedsimAgent(self):
        # update path
        painter_path = QtGui.QPainterPath()
        painter_path.setFillRule(QtCore.Qt.WindingFill)
        # get shapes from the agent and convert them to a path
        for body in self.pedsimAgent.flatlandModel.bodies.values():
            # skip safety distance circle
            if body.name == "safety_dist_circle":
                continue
            # set color
            brush = QtGui.QBrush(body.color, QtCore.Qt.BrushStyle.SolidPattern)
            self.graphicsPathItem.setBrush(brush)
            # compose path
            for footprint in body.footprints:
                if isinstance(footprint, CircleFlatlandFootprint):
                    center = QtCore.QPointF(footprint.center[0], footprint.center[1])
                    radius = footprint.radius
                    painter_path.addEllipse(center, radius, radius)
                if isinstance(footprint, PolygonFlatlandFootprint):
                    polygon = QtGui.QPolygonF([QtCore.QPointF(point[0], point[1]) for point in footprint.points])
                    painter_path.addPolygon(polygon)
        self.graphicsPathItem.setPath(painter_path)
        # update text
        self.graphicsPathItem.textItem.setPlainText(self.name_label.text())
        self.graphicsPathItem.updateTextItemPos()

    def setPedsimAgent(self, agent: PedsimAgent):
        self.pedsimAgent = agent
        self.updateEverythingFromPedsimAgent()

    def updateEverythingFromPedsimAgent(self):
        # position
        self.posXSpinBox.setValue(self.pedsimAgent.pos[0])
        self.posYSpinBox.setValue(self.pedsimAgent.pos[1])
        # waypoints
        ## remove all waypoint widgets
        for w in self.getWaypointWidgets():
            w.remove()
        ## add new waypoints
        for wp in self.pedsimAgent.waypoints:
            pos = QtCore.QPointF(wp[0], wp[1])
            self.addWaypoint(pos)
        # update name label
        self.updateNameLabelFromPedsimAgent()
        # update item scene
        self.updateGraphicsPathItemFromPedsimAgent()

    def updateNameLabelFromPedsimAgent(self):
        self.name_label.setText(self.pedsimAgent.name)

    def handleEditorSaved(self):
        # editor was saved, update possibly changed values
        self.updateNameLabelFromPedsimAgent()
        self.updateGraphicsPathItemFromPedsimAgent()

    def updateWaypointIdLabels(self):
        widgets = self.getWaypointWidgets()
        for i, w in enumerate(widgets):
            w.setId(i)

    # @pyqtSlot(QtCore.QPointF)
    def handleGraphicsViewClick(self, pos: QtCore.QPointF):
        if self.addWaypointModeActive:
            self.addWaypoint(pos)

    def addWaypoint(self, pos: QtCore.QPointF = None):
        w = WaypointWidget(self, self.graphicsScene, pos, parent=self)
        self.waypointListWidget.layout().addWidget(w)
        self.updateWaypointIdLabels()
        self.drawWaypointPath()

    def removeWaypoint(self, waypointWidget: WaypointWidget):
        self.waypointListWidget.layout().removeWidget(waypointWidget)
        self.updateWaypointIdLabels()
        self.drawWaypointPath()

    def setAddWaypointMode(self, enable: bool):
        self.addWaypointModeActive = enable
        if enable:
            self.activeModeWindow.show()
        else:
            self.activeModeWindow.hide()

    def save(self):
        # saves position and waypoints to the pedsim agent
        # all other attributes should have already been saved by the PedsimAgentEditor
        # position
        pos_x = self.posXSpinBox.value()
        pos_y = self.posYSpinBox.value()
        self.pedsimAgent.pos = np.array([pos_x, pos_y])
        # waypoints
        self.pedsimAgent.waypoints = []
        for w in self.getWaypointWidgets():
            x, y = w.getPos()
            self.pedsimAgent.waypoints.append(np.array([x, y]))

    def remove(self):
        # remove waypoints
        for w in self.getWaypointWidgets():
            w.remove()
        # remove items from scene
        self.graphicsScene.removeItem(self.graphicsPathItem)
        self.graphicsScene.removeItem(self.graphicsPathItem.textItem)
        self.graphicsScene.removeItem(self.waypointPathItem)
        del self.graphicsPathItem.keyPressEater  # delete to remove event filter
        # remove widget
        self.parent().layout().removeWidget(self)
        self.deleteLater()

    def onAddWaypointClicked(self):
        if self.addWaypointModeActive:
            self.setAddWaypointMode(False)
        else:
            self.setAddWaypointMode(True)

    def onEditClicked(self):
        self.pedsimAgentEditor.show()

    def onDeleteClicked(self):
        self.remove()



class FlatlandObjectWidget(QtWidgets.QFrame):
    '''
    This is a row in the obstacles frame.
    '''
    def __init__(self, id: int, flatlandObjectIn: FlatlandObject, graphicsScene: QtWidgets.QGraphicsScene, graphicsView: ArenaQGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.graphicsScene = graphicsScene
        self.graphicsView = graphicsView
        self.flatlandObject = flatlandObjectIn
        # self.modelPath = flatlandObjectIn.flatlandModel.path

        # create graphics path item
        self.graphicsPathItem = ArenaGraphicsPathItem(self)
        ## add to scene
        self.graphicsScene.addItem(self.graphicsPathItem)

        self.setup_ui()

        self.graphicsPathItem.textItem.setPlainText(self.name_label.text())

        self.updateEverythingFromFlatlandObject()

    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)

        # name label
        self.name_label = QtWidgets.QLabel("obstacle" + str(self.id))
        self.layout().addWidget(self.name_label, 0, 0)

        # delete button
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(self.onDeleteClicked)
        self.layout().addWidget(self.delete_button, 0, 2)

        # position
        label = QtWidgets.QLabel("Pos:")
        self.layout().addWidget(label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.posXSpinBox = ArenaQDoubleSpinBox()
        self.posXSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posXSpinBox, 1, 1)
        self.posYSpinBox = ArenaQDoubleSpinBox()
        self.posYSpinBox.valueChanged.connect(self.updateGraphicsPathItemFromSpinBoxes)
        self.layout().addWidget(self.posYSpinBox, 1, 2)

        # folder
        folder_label = QtWidgets.QLabel("Model:")
        self.layout().addWidget(folder_label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.browse_button = QtWidgets.QPushButton("Browse...")
        self.browse_button.clicked.connect(self.onBrowseClicked)
        self.layout().addWidget(self.browse_button, 2, 1, 1, -1)


    def onBrowseClicked(self):
        default_folder = get_ros_package_path("simulator_setup")
        if default_folder != "":
            default_folder = os.path.join(default_folder, "obstacles")
        res = QtWidgets.QFileDialog.getOpenFileName(self, "Select Flatland Model File", default_folder)
        path = res[0]
        if os.path.exists(path):
            # set label to show file name
            name = pathlib.Path(path).parts[-1]
            self.browse_button.setText(remove_file_ending(name))
            # update flatland object and graphics item
            self.flatlandObject.flatlandModel.load(path)
            self.updateGraphicsPathItemFromFlatlandObject()

    def handleMouseDoubleClick(self):
        # function will be called by the graphics item
        self.onBrowseClicked()

    def handleItemChange(self):
        # function will be called by the graphics item
        self.updateSpinBoxesFromGraphicsItem()

    def updateSpinBoxesFromGraphicsItem(self):
        new_pos = self.graphicsPathItem.mapToScene(self.graphicsPathItem.transformOriginPoint())
        self.posXSpinBox.setValue(new_pos.x())
        self.posYSpinBox.setValue(new_pos.y())

    def updateGraphicsPathItemFromSpinBoxes(self):
        if not self.graphicsPathItem.isDragged:  # prevents recursive loop (spin box <-> moving item)
            x = self.posXSpinBox.value()
            y = self.posYSpinBox.value()
            self.graphicsPathItem.setPosNoEvent(x, y)
            self.graphicsPathItem.updateTextItemPos()

    def updateGraphicsPathItemFromFlatlandObject(self):
        # update path
        painter_path = QtGui.QPainterPath()
        painter_path.setFillRule(QtCore.Qt.WindingFill)
        # get shapes from the agent and convert them to a path
        for body in self.flatlandObject.flatlandModel.bodies.values():
            # skip safety distance circle
            if body.name == "safety_dist_circle":
                continue
            # set color
            brush = QtGui.QBrush(body.color, QtCore.Qt.BrushStyle.SolidPattern)
            self.graphicsPathItem.setBrush(brush)
            # compose path
            for footprint in body.footprints:
                if isinstance(footprint, CircleFlatlandFootprint):
                    center = QtCore.QPointF(footprint.center[0], footprint.center[1])
                    radius = footprint.radius
                    painter_path.addEllipse(center, radius, radius)
                if isinstance(footprint, PolygonFlatlandFootprint):
                    polygon = QtGui.QPolygonF([QtCore.QPointF(point[0], point[1]) for point in footprint.points])
                    painter_path.addPolygon(polygon)
        self.graphicsPathItem.setPath(painter_path)
        # update rotation
        angle = rad_to_deg(self.flatlandObject.angle)
        self.graphicsPathItem.setRotation(angle)
        # update text
        self.graphicsPathItem.textItem.setPlainText(self.flatlandObject.name)
        self.graphicsPathItem.updateTextItemPos()

    def updateEverythingFromFlatlandObject(self):
        # position
        self.posXSpinBox.setValue(self.flatlandObject.pos[0])
        self.posYSpinBox.setValue(self.flatlandObject.pos[1])
        # update name label
        self.name_label.setText(self.flatlandObject.name)
        # update browse button
        if self.flatlandObject.flatlandModel.path == "":
            self.browse_button.setText("Browse...")
        else:
            name = pathlib.Path(self.flatlandObject.flatlandModel.path).parts[-1]
            self.browse_button.setText(remove_file_ending(name))
        # update item scene
        self.updateGraphicsPathItemFromFlatlandObject()

    def save(self):
        # saves everything to the flatland object

        # name
        # can't be edited...

        # position
        pos_x = self.posXSpinBox.value()
        pos_y = self.posYSpinBox.value()
        self.flatlandObject.pos = np.array([pos_x, pos_y])
        angle = self.graphicsPathItem.rotation()  # this is a value between -180 and 180
        self.flatlandObject.angle = deg_to_rad(angle)

        # model path
        # already updated in self.onBrowseClicked()

    def remove(self):
        # remove items from scene
        self.graphicsScene.removeItem(self.graphicsPathItem)
        self.graphicsScene.removeItem(self.graphicsPathItem.textItem)
        del self.graphicsPathItem.keyPressEater  # delete to remove event filter
        # remove widget
        self.parent().layout().removeWidget(self)
        self.deleteLater()

    def onDeleteClicked(self):
        self.remove()



class RobotAgentWidget(QtWidgets.QFrame):
    '''
    This is a row in the obstacles frame.
    '''
    def __init__(self, graphicsScene: QtWidgets.QGraphicsScene, graphicsView: ArenaQGraphicsView, **kwargs):
        super().__init__(**kwargs)
        self.graphicsScene = graphicsScene
        self.graphicsView = graphicsView

        self.setup_ui()

        # create graphics items displayed in the scene
        ## start pos
        self.startGraphicsEllipseItem = ArenaGraphicsEllipseItem(self.startXSpinBox, self.startYSpinBox, -0.25, -0.25, 0.5, 0.5)
        # set color
        brush = QtGui.QBrush(QtGui.QColor("green"), QtCore.Qt.BrushStyle.SolidPattern)
        self.startGraphicsEllipseItem.setBrush(brush)
        # enable text next to item in scene
        self.startGraphicsEllipseItem.enableTextItem(self.graphicsScene, "Robot")
        # add to scene
        self.graphicsScene.addItem(self.startGraphicsEllipseItem)

        ## goal pos
        self.goalGraphicsEllipseItem = ArenaGraphicsEllipseItem(self.goalXSpinBox, self.goalYSpinBox, -0.25, -0.25, 0.5, 0.5)
        # set color
        brush = QtGui.QBrush(QtGui.QColor("red"), QtCore.Qt.BrushStyle.SolidPattern)
        self.goalGraphicsEllipseItem.setBrush(brush)
        # enable text next to item in scene
        self.goalGraphicsEllipseItem.enableTextItem(self.graphicsScene, "Goal")
        # add to scene
        self.graphicsScene.addItem(self.goalGraphicsEllipseItem)

        # move start and goal positions a bit to make them not overlap
        self.startXSpinBox.setValue(-3)
        self.startYSpinBox.setValue(3)
        self.goalXSpinBox.setValue(3)
        self.goalYSpinBox.setValue(-3)
        
    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: rgb(255, 255, 255);")

        # name label
        self.name_label = QtWidgets.QLabel("Robot")
        self.layout().addWidget(self.name_label, 0, 0)

        # start position
        label = QtWidgets.QLabel("Start:")
        self.layout().addWidget(label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.startXSpinBox = ArenaQDoubleSpinBox()
        self.startXSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.startXSpinBox, 1, 1)
        self.startYSpinBox = ArenaQDoubleSpinBox()
        self.startYSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.startYSpinBox, 1, 2)

        # goal position
        label = QtWidgets.QLabel("Goal")
        self.layout().addWidget(label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.goalXSpinBox = ArenaQDoubleSpinBox()
        self.goalXSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.goalXSpinBox, 2, 1)
        self.goalYSpinBox = ArenaQDoubleSpinBox()
        self.goalYSpinBox.valueChanged.connect(self.updateGraphicsItemsFromSpinBoxes)
        self.layout().addWidget(self.goalYSpinBox, 2, 2)

        self.resetsSpinBox = QtWidgets.QSpinBox()
        self.resetsSpinBox.setMinimum(0)
        rst_label = QtWidgets.QLabel("Episode resets:")
        self.layout().addWidget(rst_label, 3, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(self.resetsSpinBox, 3, 1)

    def updateSpinBoxesFromGraphicsItems(self):
        # start
        new_pos = self.startGraphicsEllipseItem.mapToScene(self.startGraphicsEllipseItem.transformOriginPoint())
        self.startXSpinBox.setValue(new_pos.x())
        self.startYSpinBox.setValue(new_pos.y())
        # goal
        new_pos = self.goalGraphicsEllipseItem.mapToScene(self.goalGraphicsEllipseItem.transformOriginPoint())
        self.goalXSpinBox.setValue(new_pos.x())
        self.goalYSpinBox.setValue(new_pos.y())

    def updateGraphicsItemsFromSpinBoxes(self):
        # start
        if not self.startGraphicsEllipseItem.isDragged:  # prevents recursive loop (spin box <-> moving item)
            x = self.startXSpinBox.value()
            y = self.startYSpinBox.value()
            self.startGraphicsEllipseItem.setPosNoEvent(x, y)
        # goal
        if not self.goalGraphicsEllipseItem.isDragged:
            x = self.goalXSpinBox.value()
            y = self.goalYSpinBox.value()
            self.goalGraphicsEllipseItem.setPosNoEvent(x, y)



class ArenaScenarioEditor(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()
        self.arenaScenario = ArenaScenario()
        self.numObstacles = 0
        self.pixmap_item = None
        self.mapData = None
        self.currentSavePath = ""
        self.copied = []
        self.lastNameId = 0

        # set default map to empty map if it exists
        path = pathlib.Path(get_ros_package_path("simulator_setup")) / "maps" / "map_empty" / "map.yaml"
        if path.is_file():
            self.setMap(str(path))

        # create global pedsim settings widget
        self.pedsimAgentsGlobalConfigWidget = PedsimAgentEditorGlobalConfig()
        self.pedsimAgentsGlobalConfigWidget.editorSaved.connect(self.onPedsimAgentsGlobalConfigChanged)

    def setup_ui(self):
        self.setWindowTitle("Flatland Scenario Editor")
        self.resize(1300, 700)
        self.move(100, 100)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap('icon.png'), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)

        # set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(QtWidgets.QGridLayout())
        self.setCentralWidget(central_widget)

        # menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open...", self.onOpenClicked, "Ctrl+O")
        file_menu.addAction("Save", self.onSaveClicked, "Ctrl+S")
        file_menu.addAction("Save As...", self.onSaveAsClicked, "Ctrl+Shift+S")
        add_menu = menubar.addMenu("Elements")
        add_menu.addAction("Set Map...", self.onSetMapClicked)
        add_menu.addAction("Add Pedsim Agent", self.onAddPedsimAgentClicked, "Ctrl+1")
        add_menu.addAction("Add Flatland Object", self.onAddFlatlandObjectClicked, "Ctrl+2")
        global_pedsim_settings_menu = menubar.addMenu("Global Configs")
        global_pedsim_settings_menu.addAction("Pedsim Agents...", self.onPedsimAgentsGlobalConfigClicked)

        # status bar
        self.statusBar()  # create status bar
        
        # drawing frame
        ## frame
        drawing_frame = QtWidgets.QFrame()
        drawing_frame.setLayout(QtWidgets.QVBoxLayout())
        drawing_frame.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)
        self.centralWidget().layout().addWidget(drawing_frame, 0, 1, -1, -1)
        ## graphicsscene
        self.gscene = ArenaQGraphicsScene()
        ## graphicsview
        self.gview = ArenaQGraphicsView(self.gscene)
        self.gview.scale(0.25, 0.25)  # zoom out a bit
        drawing_frame.layout().addWidget(self.gview)

        # obstacles
        ## scrollarea
        self.obstacles_scrollarea = QtWidgets.QScrollArea(self)
        self.obstacles_scrollarea.setWidgetResizable(True)
        self.obstacles_scrollarea.setMinimumWidth(300)
        self.centralWidget().layout().addWidget(self.obstacles_scrollarea, 0, 0, -1, 1)
        ## frame
        self.obstacles_frame = QtWidgets.QFrame()
        self.obstacles_frame.setLayout(QtWidgets.QVBoxLayout())
        self.obstacles_frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.obstacles_scrollarea.setWidget(self.obstacles_frame)

        # always add robot agent
        self.robotAgentWidget = RobotAgentWidget(self.gscene, self.gview)
        self.obstacles_frame.layout().addWidget(self.robotAgentWidget)

    def onPedsimAgentsGlobalConfigClicked(self):
        self.pedsimAgentsGlobalConfigWidget.show()

    def onPedsimAgentsGlobalConfigChanged(self):
        for w in self.getPedsimAgentWidgets():
            w.save()
            global_agent = copy.deepcopy(self.pedsimAgentsGlobalConfigWidget.pedsimAgent)
            # preserve individual values
            global_agent.name = w.pedsimAgent.name
            global_agent.flatlandModel = w.pedsimAgent.flatlandModel
            global_agent.pos = w.pedsimAgent.pos
            global_agent.waypoints = w.pedsimAgent.waypoints
            # set new agent
            w.pedsimAgent = global_agent
            w.pedsimAgentEditor.pedsimAgent = global_agent
            w.pedsimAgentEditor.updateValuesFromPedsimAgent()
            w.handleEditorSaved()

    def onSetMapClicked(self):
        initial_folder = os.path.join(get_ros_package_path("simulator_setup"), "maps")
        res = QtWidgets.QFileDialog.getOpenFileName(parent=self, directory=initial_folder)
        path = res[0]
        if path != "":
            self.setMap(path)

    def setMap(self, path: str):
        self.mapData = RosMapData(path)
        pixmap = QtGui.QPixmap(self.mapData.image_path)
        transform = QtGui.QTransform.fromScale(1.0, -1.0)  # flip y axis
        pixmap = pixmap.transformed(transform)
        if self.pixmap_item != None:
            # remove old map
            self.gscene.removeItem(self.pixmap_item)
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setZValue(-1.0)  # make sure map is always in the background
        self.pixmap_item.setScale(self.mapData.resolution)
        self.pixmap_item.setOffset(self.mapData.origin[0] / self.mapData.resolution, self.mapData.origin[1] / self.mapData.resolution)
        self.gscene.addItem(self.pixmap_item)

    def getMapData(self, path: str) -> dict:
        # read yaml file containing map meta data
        with open(path, "r") as file:
            data = yaml.safe_load(file)
            return data

    def disableAddWaypointMode(self):
        widgets = self.getPedsimAgentWidgets()
        for w in widgets:
            w.setAddWaypointMode(False)

    def onAddPedsimAgentClicked(self):
        yaml_file = ""
        try:
            yaml_file = os.path.join(get_ros_package_path("simulator_setup"), "dynamic_obstacles", "person_two_legged.model.yaml")
        except:
            pass

        new_agent = PedsimAgent(self.generateName(), yaml_file)
        self.arenaScenario.pedsimAgents.append(new_agent)
        self.addPedsimAgentWidget(new_agent)

    def addPedsimAgentWidget(self, agent: PedsimAgent) -> PedsimAgentWidget:
        '''
        Adds a new pedsim agent widget with the given agent.
        Warning: self.arenaScenario is not updated. Management of self.arenaScenario happens outside of this function.
        '''
        w = PedsimAgentWidget(self.numObstacles, agent, self.gscene, self.gview, parent=self)
        self.obstacles_frame.layout().addWidget(w)
        self.numObstacles += 1
        return w

    def onAddFlatlandObjectClicked(self):
        model_path = ""
        try:
            model_path = os.path.join(get_ros_package_path("simulator_setup"), "obstacles", "shelf.yaml")
        except:
            pass

        new_object = FlatlandObject(self.generateName(), model_path)
        self.arenaScenario.staticObstacles.append(new_object)
        self.addFlatlandObjectWidget(new_object)

    def addFlatlandObjectWidget(self, object: FlatlandObject) -> FlatlandObjectWidget:
        '''
        Adds a new flatland object widget with the given agent.
        Warning: self.arenaScenario is not updated. Management of self.arenaScenario happens outside of this function.
        '''
        w = FlatlandObjectWidget(self.numObstacles, object, self.gscene, self.gview)
        self.obstacles_frame.layout().addWidget(w)
        self.numObstacles += 1
        return w

    def getFlatlandObjectWidgets(self) -> List[FlatlandObjectWidget]:
        widgets = []
        for i in range(self.obstacles_frame.layout().count()):
            w = self.obstacles_frame.layout().itemAt(i).widget()
            if w != None and isinstance(w, FlatlandObjectWidget):
                widgets.append(w)
        return widgets

    def getPedsimAgentWidgets(self):
        widgets = []
        for i in range(self.obstacles_frame.layout().count()):
            w = self.obstacles_frame.layout().itemAt(i).widget()
            if w != None and isinstance(w, PedsimAgentWidget):
                widgets.append(w)
        return widgets

    def getElementsCount(self):
        count = 0
        for i in range(self.obstacles_frame.layout().count()):
            w = self.obstacles_frame.layout().itemAt(i).widget()
            if w != None and isinstance(w, PedsimAgentWidget):
                count += 1
            if w != None and isinstance(w, FlatlandObjectWidget):
                count += 1
        return count

    def generateName(self):
        self.lastNameId += 1
        return str(self.lastNameId)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape or event.key() == QtCore.Qt.Key.Key_Return:
            self.disableAddWaypointMode()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_C:
            self.copied = self.gscene.selectedItems()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_V:
            self.pasteElements()

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier and event.key() == QtCore.Qt.Key.Key_D:
            self.toggleWaypointMode()

        return super().keyPressEvent(event)

    def toggleWaypointMode(self):
        # active waypoint mode for selected pedsim agents
        for item in self.gscene.selectedItems():
            if hasattr(item, "parentWidget"):
                widget = item.parentWidget
                if isinstance(widget, PedsimAgentWidget):
                    widget.onAddWaypointClicked()

    def pasteElements(self):
        # duplicate copied items
        for item in self.copied:
            widget = item.parentWidget
            if isinstance(widget, PedsimAgentWidget):
                widget.save()
                agent = copy.deepcopy(widget.pedsimAgent)
                agent.name = self.generateName()
                # move agent and waypoints a bit
                agent.pos[0] += 1.0
                agent.pos[1] += 1.0
                for wp in agent.waypoints:
                    wp[0] += 1.0
                    wp[1] += 1.0
                new_widget = self.addPedsimAgentWidget(agent)
                # select new item and waypoints
                new_widget.graphicsPathItem.setSelected(True)
                for w in new_widget.getWaypointWidgets():
                    w.ellipseItem.setSelected(True)
                # unselect old item and waypoints
                widget.graphicsPathItem.setSelected(False)
                for w in widget.getWaypointWidgets():
                    w.ellipseItem.setSelected(False)
            elif isinstance(widget, FlatlandObjectWidget):
                widget.save()
                obj = copy.deepcopy(widget.flatlandObject)
                obj.name = self.generateName()
                obj.pos[0] += 1.0
                obj.pos[1] += 1.0
                new_widget = self.addFlatlandObjectWidget(obj)
                # select new item
                new_widget.graphicsPathItem.setSelected(True)
                # unselect old item
                widget.graphicsPathItem.setSelected(False)

    def onNewScenarioClicked(self):
        pass

    def onOpenClicked(self):
        initial_folder = os.path.join(get_ros_package_path("simulator_setup"), "scenarios")
        res = QtWidgets.QFileDialog.getOpenFileName(parent=self, directory=initial_folder)
        path = res[0]
        if path != "":
            self.loadArenaScenario(path)

    def onSaveClicked(self):
        if not self.save():
            # no path has been set yet. fall back to "save as"
            self.onSaveAsClicked()

    def onSaveAsClicked(self) -> bool:
        initial_folder = os.path.join(get_ros_package_path("simulator_setup"), "scenarios")

        res = QtWidgets.QFileDialog.getSaveFileName(parent=self, directory=initial_folder)
        path = res[0]
        if path != "":
            return self.save(path)

        return False

    def loadArenaScenario(self, path: str):
        self.currentSavePath = path
        self.arenaScenario.loadFromFile(path)
        self.updateWidgetsFromArenaScenario()

    def save(self, path: str = "") -> bool:
        if path != "":
            self.currentSavePath = path

        self.updateArenaScenarioFromWidgets()
        if self.arenaScenario.saveToFile():
            msg = f"[{time.strftime('%H:%M:%S')}] Saved scenario to {self.arenaScenario.path}"
            self.statusBar().showMessage(msg, 10 * 1000)
            return True

        return False

    def updateWidgetsFromArenaScenario(self):
        # pedsim agents
        ## remove all pedsim widgets
        for w in self.getPedsimAgentWidgets():
            w.remove()
        ## create new pedsim widgets
        for agent in self.arenaScenario.pedsimAgents:
            self.addPedsimAgentWidget(agent)

        # static obstacles
        ## remove all flatland object widgets
        for w in self.getFlatlandObjectWidgets():
            w.remove()
        ## create new flatland object widgets
        for obstacle in self.arenaScenario.staticObstacles:
            self.addFlatlandObjectWidget(obstacle)

        # interactive obstacles
        # TODO

        # robot position
        self.robotAgentWidget.startXSpinBox.setValue(self.arenaScenario.robotPosition[0])
        self.robotAgentWidget.startYSpinBox.setValue(self.arenaScenario.robotPosition[1])
        # robot goal
        self.robotAgentWidget.goalXSpinBox.setValue(self.arenaScenario.robotGoal[0])
        self.robotAgentWidget.goalYSpinBox.setValue(self.arenaScenario.robotGoal[1])

        # map
        self.setMap(self.arenaScenario.mapPath)

        # resets
        self.robotAgentWidget.resetsSpinBox.setValue(self.arenaScenario.resets)

    def updateArenaScenarioFromWidgets(self):
        '''
        Save data from widgets into self.arenaScenario.
        '''
        # reset scenario
        self.arenaScenario.__init__()

        # save path
        self.arenaScenario.path = self.currentSavePath

        # save pedsim agents
        for w in self.getPedsimAgentWidgets():
            w.save()  # save all data from widget(s) into pedsim agent
            self.arenaScenario.pedsimAgents.append(w.pedsimAgent)  # add pedsim agent

        # save static obstacles
        for w in self.getFlatlandObjectWidgets():
            w.save()  # save all data from widget(s) into flatland object
            self.arenaScenario.staticObstacles.append(w.flatlandObject)  # add flatland object

        # save map path
        if self.mapData != None:
            self.arenaScenario.mapPath = self.mapData.path

        # robot position
        self.arenaScenario.robotPosition[0] = self.robotAgentWidget.startXSpinBox.value()
        self.arenaScenario.robotPosition[1] = self.robotAgentWidget.startYSpinBox.value()
        # robot goal
        self.arenaScenario.robotGoal[0] = self.robotAgentWidget.goalXSpinBox.value()
        self.arenaScenario.robotGoal[1] = self.robotAgentWidget.goalYSpinBox.value()

        # interactive obstacles
        # TODO
        self.arenaScenario.resets = self.robotAgentWidget.resetsSpinBox.value()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = ArenaScenarioEditor()
    widget.show()

    app.exec()
