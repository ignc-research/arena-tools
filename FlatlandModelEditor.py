from PyQt5 import QtGui, QtCore, QtWidgets
import os
import copy
from FlatlandModel import *
from FlatlandBodyEditor import FlatlandBodyEditor
from HelperFunctions import *
from FlatlandPlugin import *


class FlatlandPluginWidget(QtWidgets.QWidget):
    """
    This is a row in the plugins frame.
    """

    def __init__(self, id: int, flatland_model: FlatlandModel, **kwargs):
        super().__init__(**kwargs)
        self.setup_ui()
        self.id = id
        self.flatland_model = flatland_model

    def setup_ui(self):
        self.setLayout(QtWidgets.QGridLayout())
        layout_idx = 0

        # plugin type dropdown
        self.plugin_type_combo_box = QtWidgets.QComboBox()
        for plugin_type in FlatlandPluginType:
            self.plugin_type_combo_box.insertItem(
                plugin_type.value, plugin_type.name.lower()
            )
        self.plugin_type_combo_box.setFixedSize(150, 20)
        self.plugin_type_combo_box.currentIndexChanged.connect(
            self.on_plugin_type_changed
        )
        self.layout().addWidget(self.plugin_type_combo_box, layout_idx, 0)
        layout_idx += 1

        # pedsim movement
        ## agent topic
        ### label
        self.agent_topic_label = QtWidgets.QLabel("Agent Topic")
        self.layout().addWidget(self.agent_topic_label, layout_idx, 0)
        ### line edit
        self.agent_topic_line_edit = QtWidgets.QLineEdit("/pedsim_simulator/simulated_agents")
        self.layout().addWidget(self.agent_topic_line_edit, layout_idx, 1)
        layout_idx += 1

        ## base_body_
        ### label
        self.base_body_label = QtWidgets.QLabel("Base Body")
        self.layout().addWidget(self.base_body_label, layout_idx, 0)
        ### line edit
        self.base_body_line_edit = QtWidgets.QLineEdit("base")
        self.layout().addWidget(self.base_body_line_edit, layout_idx, 1)
        layout_idx += 1

        ## left_leg_body_
        ### label
        self.left_leg_body_label = QtWidgets.QLabel("Left Leg Body")
        self.layout().addWidget(self.left_leg_body_label, layout_idx, 0)
        ### line edit
        self.left_leg_body_line_edit = QtWidgets.QLineEdit("left_leg")
        self.layout().addWidget(self.left_leg_body_line_edit, layout_idx, 1)
        layout_idx += 1

        ## right_leg_body_
        ### label
        self.right_leg_body_label = QtWidgets.QLabel("Right Leg Body")
        self.layout().addWidget(self.right_leg_body_label, layout_idx, 0)
        ### line edit
        self.right_leg_body_line_edit = QtWidgets.QLineEdit("right_leg")
        self.layout().addWidget(self.right_leg_body_line_edit, layout_idx, 1)
        layout_idx += 1

        ## update_rate_
        ### label
        self.update_rate_label = QtWidgets.QLabel("Update Rate")
        self.layout().addWidget(self.update_rate_label, layout_idx, 0)
        ### spin box
        self.update_rate_spin_box = QtWidgets.QSpinBox()
        self.update_rate_spin_box.setValue(10)
        self.layout().addWidget(self.update_rate_spin_box, layout_idx, 1)
        layout_idx += 1

        ## leg_offset_
        ### label
        self.leg_offset_label = QtWidgets.QLabel("Leg Offset")
        self.layout().addWidget(self.leg_offset_label, layout_idx, 0)
        ### spin box
        self.leg_offset_spin_box = QtWidgets.QDoubleSpinBox()
        self.leg_offset_spin_box.setValue(0.38)
        self.layout().addWidget(self.leg_offset_spin_box, layout_idx, 1)
        layout_idx += 1

        ## step_time_
        ### label
        self.step_time_label = QtWidgets.QLabel("Step Time (s)")
        self.layout().addWidget(self.step_time_label, layout_idx, 0)
        ### spin box
        self.step_time_spin_box = QtWidgets.QDoubleSpinBox()
        self.step_time_spin_box.setValue(0.6)
        self.layout().addWidget(self.step_time_spin_box, layout_idx, 1)
        layout_idx += 1

        # posepub_
        ## body
        ### label
        self.posepub_label = QtWidgets.QLabel("Body")
        self.layout().addWidget(self.posepub_label, layout_idx, 0)
        ### line edit
        self.posepub_line_edit = QtWidgets.QLineEdit("base")
        self.layout().addWidget(self.posepub_line_edit, layout_idx, 1)
        layout_idx += 1

        ## odom_frame_id_
        ### label
        self.odom_frame_id_label = QtWidgets.QLabel("Odom Frame ID")
        self.layout().addWidget(self.odom_frame_id_label, layout_idx, 0)
        ### line edit
        self.odom_frame_id_line_edit = QtWidgets.QLineEdit("odom")
        self.layout().addWidget(self.odom_frame_id_line_edit, layout_idx, 1)
        layout_idx += 1

        ## odom_pub_
        ### label
        self.odom_pub_label = QtWidgets.QLabel("Odom Topic")
        self.layout().addWidget(self.odom_pub_label, layout_idx, 0)
        ### line edit
        self.odom_pub_line_edit = QtWidgets.QLineEdit("odom")
        self.layout().addWidget(self.odom_pub_line_edit, layout_idx, 1)
        layout_idx += 1

        ## ground_truth_pub_
        ### label
        self.ground_truth_pub_label = QtWidgets.QLabel("Ground Truth Topic")
        self.layout().addWidget(self.ground_truth_pub_label, layout_idx, 0)
        ### line edit
        self.ground_truth_pub_line_edit = QtWidgets.QLineEdit("dynamic_human")
        self.layout().addWidget(self.ground_truth_pub_line_edit, layout_idx, 1)
        layout_idx += 1

        ## pub_rate_
        ### label
        self.pub_rate_label = QtWidgets.QLabel("Publish Rate")
        self.layout().addWidget(self.pub_rate_label, layout_idx, 0)
        ### spin box
        self.pub_rate_spin_box = QtWidgets.QSpinBox()
        self.pub_rate_spin_box.setValue(10)
        self.layout().addWidget(self.pub_rate_spin_box, layout_idx, 1)
        layout_idx += 1


    def on_plugin_type_changed(self):
        # show  and hide all relevant widgets
        if self.plugin_type_combo_box.currentIndex() == FlatlandPluginType.UNDEFINED.value:
            # pedsim movement
            ## agent topic
            self.agent_topic_label.hide()
            self.agent_topic_line_edit.hide()

            ## base_body_
            self.base_body_label.hide()
            self.base_body_line_edit.hide()

            ## left_leg_body_
            self.left_leg_body_label.hide()
            self.left_leg_body_line_edit.hide()

            ## right_leg_body_
            self.right_leg_body_label.hide()
            self.right_leg_body_line_edit.hide()

            ## update_rate_
            self.update_rate_label.hide()
            self.update_rate_spin_box.hide()

            ## leg_offset_
            self.leg_offset_label.hide()
            self.leg_offset_spin_box.hide()

            ## step_time_
            self.step_time_label.hide()
            self.step_time_spin_box.hide()

            # posepub_
            ## body
            self.posepub_label.hide()
            self.posepub_line_edit.hide()

            ## odom_frame_id_
            self.odom_frame_id_label.hide()
            self.odom_frame_id_line_edit.hide()

            ## odom_pub_
            self.odom_pub_label.hide()
            self.odom_pub_line_edit.hide()

            ## ground_truth_pub_
            self.ground_truth_pub_label.hide()
            self.ground_truth_pub_line_edit.hide()

            ## pub_rate_
            self.pub_rate_label.hide()
            self.pub_rate_spin_box.hide()

        elif self.plugin_type_combo_box.currentIndex() == FlatlandPluginType.PEDSIMMOVEMENT.value:
            # pedsim movement
            ## agent topic
            self.agent_topic_label.show()
            self.agent_topic_line_edit.show()

            ## base_body_
            self.base_body_label.show()
            self.base_body_line_edit.show()

            ## left_leg_body_
            self.left_leg_body_label.show()
            self.left_leg_body_line_edit.show()

            ## right_leg_body_
            self.right_leg_body_label.show()
            self.right_leg_body_line_edit.show()

            ## update_rate_
            self.update_rate_label.show()
            self.update_rate_spin_box.show()

            ## leg_offset_
            self.leg_offset_label.show()
            self.leg_offset_spin_box.show()

            ## step_time_
            self.step_time_label.show()
            self.step_time_spin_box.show()

            # posepub_
            ## body
            self.posepub_label.hide()
            self.posepub_line_edit.hide()

            ## odom_frame_id_
            self.odom_frame_id_label.hide()
            self.odom_frame_id_line_edit.hide()

            ## odom_pub_
            self.odom_pub_label.hide()
            self.odom_pub_line_edit.hide()

            ## ground_truth_pub_
            self.ground_truth_pub_label.hide()
            self.ground_truth_pub_line_edit.hide()

            ## pub_rate_
            self.pub_rate_label.hide()
            self.pub_rate_spin_box.hide()

        elif self.plugin_type_combo_box.currentIndex() == FlatlandPluginType.VEHICLEMOVEMENT.value:
            # pedsim movement
            ## agent topic
            self.agent_topic_label.show()
            self.agent_topic_line_edit.show()

            ## base_body_
            self.base_body_label.show()
            self.base_body_line_edit.show()

            ## left_leg_body_
            self.left_leg_body_label.show()
            self.left_leg_body_line_edit.show()

            ## right_leg_body_
            self.right_leg_body_label.show()
            self.right_leg_body_line_edit.show()

            ## update_rate_
            self.update_rate_label.show()
            self.update_rate_spin_box.show()

            ## leg_offset_
            self.leg_offset_label.show()
            self.leg_offset_spin_box.show()

            ## step_time_
            self.step_time_label.show()
            self.step_time_spin_box.show()

            # posepub_
            ## body
            self.posepub_label.hide()
            self.posepub_line_edit.hide()

            ## odom_frame_id_
            self.odom_frame_id_label.hide()
            self.odom_frame_id_line_edit.hide()

            ## odom_pub_
            self.odom_pub_label.hide()
            self.odom_pub_line_edit.hide()

            ## ground_truth_pub_
            self.ground_truth_pub_label.hide()
            self.ground_truth_pub_line_edit.hide()

            ## pub_rate_
            self.pub_rate_label.hide()
            self.pub_rate_spin_box.hide()

        elif self.plugin_type_combo_box.currentIndex() == FlatlandPluginType.POSEPUB.value:
            # pedsim movement
            ## agent topic
            self.agent_topic_label.hide()
            self.agent_topic_line_edit.hide()

            ## base_body_
            self.base_body_label.hide()
            self.base_body_line_edit.hide()

            ## left_leg_body_
            self.left_leg_body_label.hide()
            self.left_leg_body_line_edit.hide()

            ## right_leg_body_
            self.right_leg_body_label.hide()
            self.right_leg_body_line_edit.hide()

            ## update_rate_
            self.update_rate_label.hide()
            self.update_rate_spin_box.hide()

            ## leg_offset_
            self.leg_offset_label.hide()
            self.leg_offset_spin_box.hide()

            ## step_time_
            self.step_time_label.hide()
            self.step_time_spin_box.hide()

            # posepub_
            ## body
            self.posepub_label.show()
            self.posepub_line_edit.show()

            ## odom_frame_id_
            self.odom_frame_id_label.show()
            self.odom_frame_id_line_edit.show()

            ## odom_pub_
            self.odom_pub_label.show()
            self.odom_pub_line_edit.show()

            ## ground_truth_pub_
            self.ground_truth_pub_label.show()
            self.ground_truth_pub_line_edit.show()

            ## pub_rate_
            self.pub_rate_label.show()
            self.pub_rate_spin_box.show()



class FlatlandBodyWidget(QtWidgets.QWidget):
    """
    This is a row in the bodies frame. It has the following elements:
        - body name label
        - edit button
        - delete button
    """

    def __init__(
        self,
        id: int,
        flatland_model: FlatlandModel,
        create_new_flatland_body=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.setup_ui()
        self.id = id
        self.model = flatland_model
        if create_new_flatland_body:
            flatland_body = FlatlandBody()
            self.model.bodies[id] = flatland_body

        self.flatland_body_editor = FlatlandBodyEditor(
            id,
            self.model.bodies[id],
            self,
            parent=self.parent(),
            flags=QtCore.Qt.WindowType.Window,
        )

    def setup_ui(self):
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # add name label
        self.name_label = QtWidgets.QLabel("new_body")
        self.layout.addWidget(self.name_label)

        # add edit button
        self.edit_button = QtWidgets.QPushButton("edit")
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.layout.addWidget(self.edit_button)

        # add delete button
        self.delete_button = QtWidgets.QPushButton("delete")
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.layout.addWidget(self.delete_button)

    def on_edit_clicked(self):
        self.flatland_body_editor.show()

    def on_delete_clicked(self):
        self.model.bodies.pop(self.id)
        self.parent().layout().removeWidget(self)
        self.deleteLater()


class FlatlandModelEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.model = None
        self.last_saved_model = None
        self.body_id = 0
        self.plugin_id = 0
        self.create_new_model()

    def setup_ui(self):
        self.setWindowTitle("Flatland Model Editor")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)
        self.move(500, 300)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(QtWidgets.QVBoxLayout())
        self.setCentralWidget(central_widget)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New Model", self.on_new_model_clicked, "Ctrl+N")
        file_menu.addAction("Open", self.on_open_clicked, "Ctrl+O")
        file_menu.addAction("Save", self.on_save_clicked, "Ctrl+S")
        file_menu.addAction("Save As...", self.on_save_as_clicked, "Ctrl+Shift+S")

        # add frame to add and edit bodies
        self.setup_bodies_frame()

        # add frame to add and edit plugins
        self.setup_plugins_frame()

        # add expanding spacer item
        spacer = QtWidgets.QSpacerItem(
            1, 1, vPolicy=QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.centralWidget().layout().addSpacerItem(spacer)

        self.resize(500, 200)

    def setup_bodies_frame(self):
        frame = QtWidgets.QFrame()
        frame.setLayout(QtWidgets.QGridLayout())

        # add title
        bodies_label = QtWidgets.QLabel("## Bodies")
        bodies_label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        frame.layout().addWidget(bodies_label, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        # add "add body" button
        self.add_body_button = QtWidgets.QPushButton("Add Body")
        self.add_body_button.setFixedSize(200, 30)
        self.add_body_button.clicked.connect(self.on_add_body_button_clicked)
        frame.layout().addWidget(
            self.add_body_button, 0, 1, QtCore.Qt.AlignmentFlag.AlignRight
        )

        # add body list
        self.bodies_list_frame = QtWidgets.QFrame()
        self.bodies_list_frame.setLayout(QtWidgets.QVBoxLayout())
        frame.layout().addWidget(self.bodies_list_frame, 1, 0, 1, -1)

        # add this frame to layout
        self.centralWidget().layout().addWidget(frame)

    def setup_plugins_frame(self):
        frame = QtWidgets.QFrame()
        frame.setLayout(QtWidgets.QGridLayout())

        # title
        label = QtWidgets.QLabel("## Plugins")
        label.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        frame.layout().addWidget(label, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        # button
        self.button = QtWidgets.QPushButton("Add Plugin")
        self.button.setFixedSize(200, 30)
        self.button.clicked.connect(self.on_add_plugin_button_clicked)
        frame.layout().addWidget(self.button, 0, 1, QtCore.Qt.AlignmentFlag.AlignRight)

        # plugin list
        self.plugins_list_frame = QtWidgets.QFrame()
        self.plugins_list_frame.setLayout(QtWidgets.QVBoxLayout())
        frame.layout().addWidget(self.plugins_list_frame, 1, 0, 1, -1)

        # add this frame to layout
        self.centralWidget().layout().addWidget(frame)

    def on_add_plugin_button_clicked(self):
        w = FlatlandPluginWidget(self.plugin_id, self.model, parent=self)
        w.on_plugin_type_changed()
        return self.add_flatland_plugin_widget(w)

    def add_flatland_plugin_widget(self, w: FlatlandPluginWidget):
        self.plugins_list_frame.layout().addWidget(w)
        self.plugin_id += 1
        return w

    def get_body_widgets(self):
        widgets = []
        for i in range(self.bodies_list_frame.layout().count()):
            w = self.bodies_list_frame.layout().itemAt(i).widget()
            if w != None:
                widgets.append(w)
        return widgets

    def remove_all_bodies(self):
        widgets = self.get_body_widgets()
        for widget in widgets:
            widget.on_delete_clicked()
        self.body_id = 0

    def on_new_model_clicked(self):
        if self.last_saved_model != self.model and len(self.model.bodies) > 0:
            # ask user if she wants to save changes
            msg_box = QtWidgets.QMessageBox()
            msg_box.setText("Do you want to save changes?")
            msg_box.setStandardButtons(
                QtWidgets.QMessageBox.Save
                | QtWidgets.QMessageBox.Discard
                | QtWidgets.QMessageBox.Cancel
            )
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = msg_box.exec()
            if ret == QtWidgets.QMessageBox.Save:
                if not self.on_save_as_clicked():
                    # save as dialog was cancelled
                    return
            elif ret == QtWidgets.QMessageBox.Discard:
                pass
            elif ret == QtWidgets.QMessageBox.Cancel:
                return
        self.create_new_model()

    def create_new_model(self):
        self.remove_all_bodies()
        self.model = FlatlandModel()

    def on_add_body_button_clicked(self):
        w = FlatlandBodyWidget(self.body_id, self.model, parent=self)
        return self.add_flatland_body_widget(w)

    def add_flatland_body_widget(self, w: FlatlandBodyWidget):
        self.bodies_list_frame.layout().addWidget(w)
        self.body_id += 1
        return w

    def on_open_clicked(self):
        initial_folder = os.path.join(
            get_ros_package_path("simulator_setup"), "dynamic_obstacles"
        )
        res = QtWidgets.QFileDialog.getOpenFileName(
            parent=self, directory=initial_folder
        )
        path = res[0]
        if path != "":
            self.load_model(path)

    def load_model(self, path):
        self.setWindowTitle(path.split("/")[-1])
        self.remove_all_bodies()
        self.model.load(path)
        for _ in self.model.bodies.values():
            w = FlatlandBodyWidget(
                self.body_id, self.model, create_new_flatland_body=False, parent=self
            )
            self.add_flatland_body_widget(w)

        self.last_saved_model = copy.deepcopy(self.model)

    def on_save_clicked(self):
        if self.model.save():
            self.last_saved_model = copy.deepcopy(self.model)
        else:
            # no path has been set yet. fall back to "save as"
            if self.on_save_as_clicked():
                self.last_saved_model = copy.deepcopy(self.model)

    def on_save_as_clicked(self):
        initial_folder = os.path.join(
            get_ros_package_path("simulator_setup"), "dynamic_obstacles"
        )

        res = QtWidgets.QFileDialog.getSaveFileName(
            parent=self, directory=initial_folder
        )
        path = res[0]
        if path != "":
            self.model.save(path)
            self.last_saved_model = copy.deepcopy(self.model)
            return True
        else:
            return False

    # def closeEvent(self, event: QtGui.QCloseEvent):
    #     if self.last_saved_model != self.model and len(self.model.bodies) > 0:
    #         # ask user if she wants to save changes
    #         msg_box = QtWidgets.QMessageBox()
    #         msg_box.setText("Do you want to save changes?")
    #         msg_box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
    #         msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
    #         ret = msg_box.exec()
    #         if ret == QtWidgets.QMessageBox.Save:
    #             self.on_save_as_clicked()
    #         elif ret == QtWidgets.QMessageBox.Discard:
    #             pass
    #         elif ret == QtWidgets.QMessageBox.Cancel:
    #             event.ignore()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = FlatlandModelEditor()
    widget.on_add_plugin_button_clicked()
    widget.show()

    app.exec()
