from PyQt5 import QtGui, QtCore, QtWidgets
import json
import pathlib
from HelperFunctions import *
from QtExtensions import *
from ArenaScenarioEditor import RosMapData


class RobotPath:
    def __init__(self):
        self.initial_pos = [0, 0]
        self.subgoals = []  # list of points [x, y]

    def toDict(self):
        d = {}
        d["initial_pos"] = self.initial_pos
        d["subgoals"] = self.subgoals
        return d


class PathData:
    def __init__(self):
        # path to map file
        self.map_path = ""
        # dict of paths; key: ID of path, value: RobotPath object
        self.robot_paths = {}

        self.num_images = 0

    def toDict(self):
        d = {}
        d["map_path"] = self.map_path
        d["num_images"] = self.num_images
        path_list = []
        for robot_path in self.robot_paths.values():
            path_list.append(robot_path.toDict())
        d["robot_paths"] = path_list
        return d

    def saveToFile(self, path_in: str):
        with open(path_in, "w") as file:
            data = self.toDict()
            json.dump(data, file, indent=4)


class PathCreator(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # add graphicsscene and graphicsview
        self.scene = ArenaQGraphicsScene()
        self.view = ArenaQGraphicsView(self.scene)
        self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setSceneRect(-1000, -1000, 2000, 2000)
        self.view.fitInView(
            QtCore.QRectF(-1.5, -1.5, 25, 25),
            mode=QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        )
        # self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setup_ui()

        # Map variables
        self.pixmap_item = None
        self.map_data = None
        # path data
        self.path_data = PathData()
        self.current_path_id = 1
        self.num_paths = 1
        # subgoal items
        self.subgoal_items = []

        # setup robot in scene
        self.robot_ellipse_item = ArenaGraphicsEllipseItem(
            None,
            None,
            -0.25,
            -0.25,
            0.5,
            0.5,
            handlePositionChangeMethod=lambda _: self.drawWaypointPath(),
        )
        ## start pos
        self.robot_ellipse_item.setPosNoEvent(0, 0)
        ## set color
        brush = QtGui.QBrush(QtGui.QColor("green"), QtCore.Qt.BrushStyle.SolidPattern)
        self.robot_ellipse_item.setBrush(brush)
        ## enable text next to item in scene
        self.robot_ellipse_item.enableTextItem(self.scene, "Robot")
        ## add to scene
        self.scene.addItem(self.robot_ellipse_item)

        # setup waypoints
        self.addWaypointModeActive = False
        self.activeModeWindow = ActiveModeWindow(self)
        self.activeModeWindow.move(1200, 200)
        self.view.clickedPos.connect(self.handleGraphicsViewClick)
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
        self.scene.addItem(self.waypointPathItem)

    def setup_ui(self):
        self.setWindowTitle("Path Creator")
        self.resize(1100, 600)
        self.move(100, 100)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        layout_index = 0

        # set central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(QtWidgets.QGridLayout())
        self.setCentralWidget(central_widget)

        # splitter
        self.splitter = QtWidgets.QSplitter()
        self.centralWidget().layout().addWidget(self.splitter)

        # left side frame
        frame = QtWidgets.QFrame()
        # frame.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Raised)
        frame.setLayout(QtWidgets.QGridLayout())
        frame.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.splitter.addWidget(frame)

        # select map
        ## label
        map_label = QtWidgets.QLabel("### Map:")
        map_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        frame.layout().addWidget(map_label, layout_index, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        ## map name label
        self.map_name_label = QtWidgets.QLabel("No map selected")
        self.map_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        frame.layout().addWidget(self.map_name_label, layout_index, 1, 1, 1)
        ## browse button
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self.onBrowseMapsClicked)
        frame.layout().addWidget(browse_button, layout_index, 3, QtCore.Qt.AlignmentFlag.AlignRight)
        layout_index += 1

        ## line
        frame.layout().addWidget(Line(), layout_index, 0, 1, -1)
        layout_index += 1

        # No. images
        ## label
        num_images_label = QtWidgets.QLabel("### No. Images")
        num_images_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        frame.layout().addWidget(
            num_images_label, layout_index, 0, QtCore.Qt.AlignmentFlag.AlignLeft
        )
        ## spinbox
        self.num_images_spin_box = QtWidgets.QSpinBox()
        self.num_images_spin_box.setRange(1, 10000)
        self.num_images_spin_box.setValue(101)
        self.num_images_spin_box.setSingleStep(1)
        self.num_images_spin_box.setFixedSize(150, 30)
        frame.layout().addWidget(
            self.num_images_spin_box, layout_index, 3, QtCore.Qt.AlignmentFlag.AlignRight
        )
        layout_index += 1
        ## line
        frame.layout().addWidget(Line(), layout_index, 0, 1, -1)
        layout_index += 1

        # prev button
        self.prev_button = QtWidgets.QPushButton("<")
        self.prev_button.clicked.connect(self.onPrevClicked)
        self.prev_button.setEnabled(False)
        frame.layout().addWidget(self.prev_button, layout_index, 0, 1, 1)
        # path name label
        self.path_name_label = QtWidgets.QLabel("Path 1")
        self.path_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        frame.layout().addWidget(self.path_name_label, layout_index, 1, 1, 1)
        # next button
        self.next_button = QtWidgets.QPushButton(">")
        self.next_button.clicked.connect(self.onNextClicked)
        self.next_button.setEnabled(False)
        frame.layout().addWidget(self.next_button, layout_index, 2, 1, 1)
        # new path button
        button = QtWidgets.QPushButton("New Path")
        button.clicked.connect(self.onNewPathClicked)
        frame.layout().addWidget(button, layout_index, 3, 1, 1)
        layout_index += 1

        # add subgoals button
        button = QtWidgets.QPushButton("Add Subgoals...")
        button.clicked.connect(self.onAddSubgoalsClicked)
        frame.layout().addWidget(button, layout_index, 0, 1, -1)
        layout_index += 1
        # line
        frame.layout().addWidget(Line(), layout_index, 0, 1, -1)
        layout_index += 1

        # save as JSON button
        button = QtWidgets.QPushButton("Save As JSON...")
        button.setFixedHeight(50)
        button.clicked.connect(self.onSaveAsJsonClicked)
        frame.layout().addWidget(button, layout_index, 0, 1, -1)
        layout_index += 1

        # add expanding spacer item
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        frame.layout().addWidget(spacer, layout_index, 0, -1, -1)
        layout_index += 1

        # right side graphicsview
        self.splitter.addWidget(self.view)

        # set splitter sizes
        self.splitter.setSizes([300, 700])

    def onBrowseMapsClicked(self):
        initial_folder = pathlib.Path.home()

        sim_setup_path = get_ros_package_path("simulator_setup")
        if sim_setup_path != "":
            initial_folder = pathlib.Path(sim_setup_path) / "maps"

        res = QtWidgets.QFileDialog.getOpenFileName(
            parent=self, caption="Select map.yaml File", directory=str(initial_folder)
        )
        path = res[0]
        if path != "":
            self.setMap(path)

    def onPrevClicked(self):
        self.saveCurrentPath()
        self.clearPath()
        self.current_path_id -= 1
        self.setPath(self.current_path_id)
        self.drawWaypointPath()

    def onNextClicked(self):
        self.saveCurrentPath()
        self.clearPath()
        self.current_path_id += 1
        self.setPath(self.current_path_id)
        self.drawWaypointPath()

    def onNewPathClicked(self):
        self.saveCurrentPath()
        self.clearPath()
        self.num_paths += 1
        self.current_path_id = self.num_paths
        self.setPath(self.current_path_id)

    def onAddSubgoalsClicked(self):
        # toggle addWaypointModeActive
        if self.addWaypointModeActive:
            self.setAddWaypointMode(False)
        else:
            self.setAddWaypointMode(True)

    def onSaveAsJsonClicked(self):
        self.saveCurrentPath()
        # write num images to data model
        self.path_data.num_images = self.num_images_spin_box.value()

        # get save file name
        initial_folder = pathlib.Path.home()
        sim_setup_path = get_ros_package_path("simulator_setup")
        if sim_setup_path != "":
            initial_folder = pathlib.Path(sim_setup_path)
        res = QtWidgets.QFileDialog.getSaveFileName(
            parent=self, caption="Select map.yaml File", directory=str(initial_folder)
        )
        path = res[0]
        if path != "":
            self.path_data.saveToFile(path)

    def clearPath(self):
        # reset current path
        # the data model is not cleared
        for item in self.subgoal_items:
            self.scene.removeItem(item)
        self.subgoal_items.clear()
        self.drawWaypointPath()

    def saveCurrentPath(self):
        path = RobotPath()
        # add robot initial pos
        path.initial_pos = [
            self.robot_ellipse_item.scenePos().x(),
            self.robot_ellipse_item.scenePos().y(),
        ]
        # add subgoals
        path.subgoals = [[item.scenePos().x(), item.scenePos().y()] for item in self.subgoal_items]
        self.path_data.robot_paths[self.current_path_id] = path

    def setPath(self, path_id: int):
        # update name label
        self.path_name_label.setText(f"Path {path_id}")
        # update enabled state of prev and next buttons
        if path_id == 1:
            self.prev_button.setEnabled(False)
        else:
            self.prev_button.setEnabled(True)
        if path_id == self.num_paths:
            self.next_button.setEnabled(False)
        else:
            self.next_button.setEnabled(True)
        # load path from model
        if path_id in self.path_data.robot_paths:
            # set robot pos
            robot_pos = self.path_data.robot_paths[path_id].initial_pos
            self.robot_ellipse_item.setPosNoEvent(robot_pos[0], robot_pos[1])
            # add subgoals
            for pos in self.path_data.robot_paths[path_id].subgoals:
                self.addWaypoint(QtCore.QPointF(pos[0], pos[1]))
        # update scene
        self.drawWaypointPath()

    def handleGraphicsViewClick(self, pos: QtCore.QPointF):
        if self.addWaypointModeActive:
            self.addWaypoint(pos)

    def addWaypoint(self, pos: QtCore.QPointF = None):
        item = SubgoalEllipseItem(self, None, None, -0.25, -0.25, 0.5, 0.5)
        item.setPosNoEvent(pos.x(), pos.y())
        self.subgoal_items.append(item)
        self.scene.addItem(item)
        self.drawWaypointPath()

    def removeWaypoint(self, item: SubgoalEllipseItem):
        # remove item from scene
        self.scene.removeItem(item)
        # remove subgoal from data
        self.subgoal_items.remove(item)
        # update path item
        self.drawWaypointPath()

    def drawWaypointPath(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.robot_ellipse_item.scenePos())
        for item in self.subgoal_items:
            path.lineTo(item.scenePos())

        self.waypointPathItem.setPath(path)

    def setAddWaypointMode(self, enable: bool):
        # set the value of addSubgoalModeActive and show/hide a small window depending on the state
        self.addWaypointModeActive = enable
        if enable:
            self.activeModeWindow.show()
        else:
            self.activeModeWindow.hide()

    def setMap(self, path: str):
        """
        Load map from map.yaml file.
        args:
            - path: path to map.yaml file
        """
        self.map_data = RosMapData(path)
        self.path_data.map_path = path
        pixmap = QtGui.QPixmap(self.map_data.image_path)
        transform = QtGui.QTransform.fromScale(1.0, -1.0)  # flip y axis
        pixmap = pixmap.transformed(transform)

        # remove old map
        if self.pixmap_item != None:
            self.scene.removeItem(self.pixmap_item)

        self.pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setZValue(-1.0)  # make sure map is always in the background
        self.pixmap_item.setScale(self.map_data.resolution)
        self.pixmap_item.setOffset(
            self.map_data.origin[0] / self.map_data.resolution,
            self.map_data.origin[1] / self.map_data.resolution,
        )
        self.scene.addItem(self.pixmap_item)

        # update label
        self.map_name_label.setText(pathlib.Path(path).parts[-2])

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape or event.key() == QtCore.Qt.Key.Key_Return:
            self.setAddWaypointMode(False)

        if (
            event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
            and event.key() == QtCore.Qt.Key.Key_D
        ):
            self.onAddSubgoalsClicked()

        return super().keyPressEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = PathCreator()
    widget.show()

    app.exec()
