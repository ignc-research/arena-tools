"""This file converts arena-scenarios, created in the pedsim-format, into the scenario format, originally used by arena-rosnav
"""

import json
from os import walk

# add the dir from which to convert the files and 'temp' to were the converted files should saved for further inspections
dir = '/home/elias/Desktop/test'
temp = '/home/elias/arena_ws/src/arena-rosnav/simulator_setup/scenarios/eval_feb_2022/temp'

filenames = next(walk(dir), (None, None, []))[2]

for path_to_json_file in filenames:
    # path_to_json_file = '/home/elias/catkin_ws/src/arena-rosnav-3D/simulator_setup/scenarios/ignc_obs05.json'
    def import_scenario_json(path_to_json_file):
        with open(path_to_json_file) as f:
            return json.load(f)
    json_ped = import_scenario_json(f'{dir}/{path_to_json_file}')
    scenario = {}
    x = {}
    x['scene_name'] = f'scenario_1'
    x['repeats'] = json_ped['resets']
    obs_list = []
    dynamic_obstacles = {}
    watchers = {}
    for i, agent in enumerate(json_ped['pedsim_agents']):
        # transforom obs
        obs = {}
        obs['obstacle_radius'] = 0.3
        obs['linear_velocity'] = agent['vmax']
        obs['type'] = 'circle'
        obs['start_pos'] = [*agent['pos'], 0.0]
        # setting relative waypoint (+ rm last waypoint which is == start point)
        obs['waypoints'] = [[point[0]-agent['pos'][0], point[1]-agent['pos'][1], 0.0 ] for point in agent['waypoints'][:-1]]
        obs['is_waypoint_relative'] = True
        obs['mode'] = 'yoyo'
        obs['triggers'] = []#[f'watcher_{i}']
        dynamic_obstacles[f'dynamic_obs_{i}'] = obs
        # transform watcher
        elmnt = {}
        elmnt['pos'] = [agent['pos'][0], agent['pos'][1]]
        elmnt['range'] = 5
        watchers[f'watcher_{i}'] = elmnt
    robot = {}
    robot['start_pos'] = [*json_ped['robot_position'], 0.0]
    robot['goal_pos'] = [*json_ped['robot_goal'], 0.0]
    x['dynamic_obstacles'] = dynamic_obstacles
    x['static_obstacles'] = {}
    x['robot'] = robot
    x['watchers'] = watchers
    scenario['scenarios'] = [x]
    # scenario['format'] = "not-arena-tools"
    with open(f'{temp}/{path_to_json_file}', 'w') as fp:
        json.dump(scenario, fp)