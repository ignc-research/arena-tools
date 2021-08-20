from enum import Enum


class FlatlandPluginType(Enum):
    UNDEFINED = 0
    PEDSIMMOVEMENT = 1
    VEHICLEMOVEMENT = 2
    POSEPUB = 3


class FlatlandPlugin:
    def __init__(self):
        self.plugin_type = FlatlandPluginType.UNDEFINED
        self.name = ""


class PedsimMovementPlugin(FlatlandPlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = FlatlandPluginType.PEDSIMMOVEMENT
        self.agent_topic = "/pedsim_simulator/simulated_agents"
        self.base_body = "base"
        self.left_leg_body = "left_leg"
        self.right_leg_body = "right_leg"
        self.safety_dist_body = "safety_dist_circle"
        self.update_rate = 10
        self.toggle_leg_movement = True
        self.leg_offset = 0.38
        self.var_leg_offset = 0.0
        self.step_time = 0.6  # seconds
        self.var_step_time = 0.00
        self.leg_radius = 0.13
        self.var_leg_radius = 0.00
        self.safety_dist = 0.7


class VehicleMovementPlugin(FlatlandPlugin):
    def __init__(self):
        super().__init__()
        self.agent_topic = "/pedsim_simulator/simulated_agents"
        self.base_body = "base"
        self.update_rate = 10
        self.safety_dist_body = "safety_dist_circle"
        self.safety_dist = 1.8


class PosePubPlugin(FlatlandPlugin):
    def __init__(self):
        super().__init__()
        self.body = "base"
        self.odom_frame_id = "odom"
        self.odom_pub = "odom"  # topic odom is published on
        self.ground_truth_pub = "dynamic_human"
        self.pub_rate = 10
