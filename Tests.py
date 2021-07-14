from ArenaScenarioEditor import *
from HelperFunctions import *

def add_obstacle_test():
    app = QtWidgets.QApplication([])

    widget = ArenaScenarioEditor()
    widget.onAddPedsimAgentClicked()
    widget.show()

    app.exec()


def edit_agent_test():
    app = QtWidgets.QApplication([])

    widget = ArenaScenarioEditor()
    widget.setMap(get_ros_package_path("simulator_setup") + "/maps/map1/map.yaml")
    widget.onAddPedsimAgentClicked()

    pedsim_widget = widget.getPedsimAgentWidgets()[0]
    pedsim_widget.pedsimAgentEditor.setModelPath(get_ros_package_path("simulator_setup") + "/dynamic_obstacles/big_forklift.model.yaml")
    pedsim_widget.pedsimAgentEditor.onSaveClicked()
    pedsim_widget.addWaypoint(QtCore.QPointF(3, 4))
    pedsim_widget.onEditClicked()
    

    widget.show()
    app.exec()

def save_test():
    app = QtWidgets.QApplication([])
    widget = ArenaScenarioEditor()
    widget.onAddPedsimAgentClicked()
    widget.onAddPedsimAgentClicked()
    widget.setMap(get_ros_package_path("simulator_setup") + "/maps/map1/map.yaml")
    widget.currentSavePath = get_ros_package_path("simulator_setup") + "/scenarios/test_scenario.json"
    # widget.arenaScenario.pedsimAgents.append(PedsimAgent())
    widget.onSaveClicked()

if __name__ == "__main__":
    add_obstacle_test()
    # edit_agent_test()
    # save_test()
    