def get_ros_package_path(package_name: str) -> str:
    try:
        import rospkg

        rospack = rospkg.RosPack()
        return rospack.get_path(package_name)
    except:
        return ""


def get_nth_decimal_part(x: float, n: int) -> int:
    """
    Get the n'th decimal part of a decimal number.
    Example:
        get_nth_decimal_part(1.234, 2) == 3
    """
    x *= 10**n  # push relevant part directly in front of decimal point
    x %= 10  # remove parts left of the relevant part
    return int(x)  # remove decimal places


def round_to_closest_20th(x: float) -> float:
    """
    Round to X.X0 or X.X5.
    Example:
        round_one_and_half_decimal_places(1.234) == 1.25
    """
    return round(x * 20) / 20


def rad_to_deg(angle: float) -> float:
    import math

    angle = normalize_angle_rad(angle)
    angle = 360.0 * angle / (2.0 * math.pi)
    return angle


def deg_to_rad(angle: float) -> float:
    import math

    angle = normalize_angle_deg(angle)
    angle = 2 * math.pi * angle / 360.0
    return angle


def normalize_angle_deg(angle: float) -> float:
    import math

    # make sure angle is positive
    while angle < 0:
        angle += 360

    # make sure angle is between 0 and 360
    angle = math.fmod(angle, 360.0)
    return angle


def normalize_angle_rad(angle: float) -> float:
    import math

    # make sure angle is positive
    while angle < 0:
        angle += 2 * math.pi
    # make sure angle is between 0 and 2 * pi
    angle = math.fmod(angle, 2 * math.pi)
    return angle


def normalize_angle(angle: float, rad: bool = True) -> float:
    if rad:
        return normalize_angle_rad(angle)
    else:
        return normalize_angle_deg(angle)


def get_current_user_path(path_in: str) -> str:
    """
    Convert a path from another user to the current user, for example:
    "/home/alice/catkin_ws" -> "/home/bob/catkin_ws"
    """
    if path_in == "":
        return ""
    from pathlib import Path

    path = Path(path_in)
    new_path = Path.home().joinpath(*path.parts[3:])
    return str(new_path)


def remove_file_ending(file_name: str) -> str:
    """
    Remove everything after the first "." in a string.
    """
    file_ending_index = file_name.find(".")
    if file_ending_index != -1:
        return file_name[:file_ending_index]
    return file_name


def create_model_config(path_in: str, model_name: str):
    """
    create_model_config creates sdf config file for a given model/mesh


    Args:
        path_in (str): desired path of the config file
        model_name (str): name of the model
    """
    from lxml import etree

    sdf = f'<model> <name>{model_name}</name> <version>1.0</version> <sdf version="1.6">model.sdf</sdf> <author> <name></name> <email></email> </author> <description></description></model>'
    root = etree.fromstring(sdf)
    tree = etree.ElementTree(root)
    tree.write(
        path_in + "model.config",
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )


def create_model_sdf(path_in: str, model_name: str):
    """
    create_model_sdf creates sdf file of the desired model/mesh

    Args:
        path_in (str): desired path to the sdf file
        model_name (str): name of the desired model/mesh
    """
    from lxml import etree
    from lxml.etree import Element
    from copy import deepcopy

    sdf = Element("sdf", version="1.6")
    model = Element("model", name=model_name)
    static = Element("static")
    static.text = "true"
    model.append(static)
    link = Element("link", name="body")
    visual = Element("visual", name="visual")
    pose = Element("pose", frame="")
    pose.text = "0 0 0 0 0 0"
    visual.append(pose)
    geometry = Element("geometry")
    mesh = Element("mesh")
    uri = Element("uri")
    uri.text = f"model://{model_name}/meshes/{model_name}.dae"
    mesh.append(uri)
    geometry.append(mesh)
    visual.append(deepcopy(geometry))
    collision = Element("collision", name="collision1")
    collision.append(geometry)
    link.append(visual)
    link.append(collision)
    model.append(link)
    sdf.append(model)
    tree = etree.ElementTree(sdf)
    tree.write(
        path_in + "model.sdf", pretty_print=True, xml_declaration=True, encoding=None
    )


def createWorldFile(path: str, map_name: str, x: float, y: float):
    """
    createWorldFile creates Gazebo world file in desired directory

    Args:
        path (str): path to the desired directory
        map_name (str): name of the world
        x (float): offset of the mesh in x direction
        y (float): offset of the mesh in y direction
    """
    from lxml import etree

    sdf = f'<sdf version="1.4"><world name="default"><include><uri>model://ground_plane</uri></include><include><uri>model://sun</uri></include><scene><ambient>0.0 0.0 0.0 1.0</ambient><shadows>0</shadows></scene><model name="my_mesh"><static>true</static><link name="body"><visual name="visual"><pose frame="">-{str(x)} -{str(y)} 1 0 0 0</pose><geometry><mesh><uri>//map.dae</uri></mesh></geometry></visual><collision name="collision1"><pose frame="">-{str(x)} -{str(y)} 1 0 0 0</pose><geometry><mesh><uri>//map.dae</uri></mesh></geometry></collision></link></model></world></sdf>'
    root = etree.fromstring(sdf)
    tree = etree.ElementTree(root)
    tree.write(
        path + map_name + ".world",
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
    )


def createObstacleFile(
    map_path: str,
    map_name: str,
    use_map_origin: bool,
    scenario_path: str,
    scenario_name: str,
):
    import yaml
    import os.path
    import numpy as np
    import xml.etree.ElementTree as xml
    import skimage.io as io
    from xml.dom import minidom

    def get_window(image, x, y):
        """
        Returns a window around a pixel.
        The windows is a 3x3 window centered around pixel (x, y). If the pixel is
        close to the edges of the image, the window will be smaller, accordingly
        (e.g., the method will return only a 2x2 window for pixel (0, 0)).
            Parameters:
                image (array_like): an image from which the window is extracted
                x (int): x coordinate of the pixel
                y (int): y coordinate of the pixel
            Returns:
                window (array_like): a window around the pixel (x, y)
        """
        sz = image.shape
        assert (
            x >= 0 and x < sz[0] and y >= 0 and y < sz[1]
        ), "Pixel indeces out of image bounds (%d, %d)" % (x, y)

        x_min = np.maximum(0, x - 1)
        x_max = np.minimum(sz[0], x + 2)
        y_min = np.maximum(0, y - 1)
        y_max = np.minimum(sz[1], y + 2)

        return image[x_min:x_max, y_min:y_max]

    def add_waypoint(scenario, id, x, y, r):
        """Adds to a scenario a waypoint named 'id' in (x, y) with radius 'r'"""
        waypoint = xml.SubElement(scenario, "waypoint")
        waypoint.set("id", str(id))
        waypoint.set("x", str(x))
        waypoint.set("y", str(y))
        waypoint.set("r", str(r))

    def add_agent(scenario, x, y, waypoints, n=2, dx=0.5, dy=0.5, type=1):
        """Adds to a scenario n agents going from (x, y) through the waypoints"""
        agent = xml.SubElement(scenario, "agent")
        agent.set("x", str(x))
        agent.set("y", str(y))
        agent.set("n", str(n))
        agent.set("dx", str(dx))
        agent.set("dy", str(dy))
        agent.set("type", str(type))
        for id in waypoints:
            addwaypoint = xml.SubElement(agent, "addwaypoint")
            addwaypoint.set("id", str(id))

    def add_waypoints_and_agent(scenario, agents_info):
        """Adds to a scenario a set of waypoints and agents going through them"""
        waypoints = agents_info["waypoints"]
        for id in waypoints.keys():
            w = waypoints[id]
            add_waypoint(scenario, id, w[0], w[1], w[2])

        agents_keys = agents_info.keys()
        agents_keys.remove("waypoints")
        for key in agents_keys:
            agent = agents_info[key]
            agent_dx = agent["dx"] if "dx" in agent else 0.5
            agent_dy = agent["dy"] if "dy" in agent else 0.5
            agent_type = agent["type"] if "type" in agent else 1
            add_agent(
                scenario,
                agent["x"],
                agent["y"],
                agent["w"],
                n=agent["n"],
                dx=agent_dx,
                dy=agent_dy,
                type=agent_type,
            )

    def add_obstacle(scenario, x1, y1, x2, y2):
        """Adds to a scenario an obstacle going from (x1, y1) to (x2, y2)"""
        obstacle = xml.SubElement(scenario, "obstacle")
        obstacle.set("x1", str(x1))
        obstacle.set("y1", str(y1))
        obstacle.set("x2", str(x2))
        obstacle.set("y2", str(y2))

    def add_pixel_obstacle(scenario, x, y, resolution):
        """Adds to a scenario a 1x1 obstacle at location (x, y)"""
        add_obstacle(
            scenario,
            x + resolution / 2,
            y - resolution / 2,
            x - resolution / 2,
            y + resolution / 2,
        )

    def scenario_from_map(map_image, map_metadata, use_map_origin=False):
        """
        Builds a pedsim scenario having obstacles to separate free space in the map
        from unknown and occupied space. Everything below 'free_thresh' (in the map
        metadata) is considered free space.
            Parameters:
                map_image (array_like): the map ternary image
                map_metadata (dictionary): the metadata extracted from the map YAML
                    file
                use_map_origin (bool): if True reads the map origin from
                    map_metadata, otherwise sets it to [0, 0, 0] (default).
                    Integration with pedsim_ros works better in the latter case.
            Returns:
                scenario (ElementTree): a pedsim scenario as xml element tree
                map_walls (array_like): a binary image showing the locations on the
                    map where obstacles have been placed
        """
        resolution = map_metadata["resolution"]
        negate = map_metadata["negate"]
        free_thresh = map_metadata["free_thresh"] * 255
        origin = map_metadata["origin"] if use_map_origin else [0.0, 0.0, 0.0]

        # ROS maps have white (255) as free space for visualization, colors need to
        # be inverted before comparing with thresholds (if negate == 0)
        if ~negate:
            map_binary = 255 - map_image < free_thresh
        else:
            map_binary = map_image < free_thresh

        scenario = xml.Element("scenario")

        sz = map_binary.shape
        map_walls = np.zeros(sz, dtype=bool)

        # reduce the search space to only the area where there is free space
        x_free = np.nonzero(np.sum(map_binary, axis=1))[0]
        x_min = np.maximum(0, x_free[0] - 1)
        x_max = np.minimum(sz[0], x_free[-1] + 2)
        y_free = np.nonzero(np.sum(map_binary, axis=0))[0]
        y_min = np.maximum(0, y_free[0] - 1)
        y_max = np.minimum(sz[1], y_free[-1] + 2)

        for x in range(x_min, x_max):
            for y in range(y_min, y_max):
                is_free = map_binary[x, y]
                window = get_window(map_binary, x, y)
                if ~is_free.any() and np.any(window) and np.any(~window):
                    # conversion between world coordinates and pixel coordinates
                    # (x and y coordinates are inverted, and y is also flipped)
                    world_x = origin[0] + y * resolution
                    world_y = origin[1] - (x - sz[0]) * resolution

                    add_pixel_obstacle(scenario, world_x, world_y, resolution)
                    map_walls[x, y] = True

        return scenario, map_walls

    def write_xml(tree, file_path, indent="  "):
        """Takes an xml tree and writes it to a file, indented"""
        indented_xml = minidom.parseString(xml.tostring(tree)).toprettyxml(
            indent=indent
        )

        with open(file_path, "w") as f:
            f.write(indented_xml)

    with open(os.path.join(map_path, map_name)) as file:
        map_metadata = yaml.safe_load(file)

    map_image = io.imread(os.path.join(map_path, map_metadata["image"]))

    print("Loaded map in " + os.path.join(map_path, map_name) + " with metadata:")
    print(map_metadata)

    scenario, map_walls = scenario_from_map(map_image, map_metadata, use_map_origin)

    # uncomment for a visualization of where the obstacles have been placed
    io.imsave(os.path.join(scenario_path, "walls.png"), map_walls * 255)

    print("Writing scene in " + os.path.join(scenario_path, scenario_name) + "...")

    write_xml(scenario, os.path.join(scenario_path, scenario_name))

    print("Done.")

    # Regarding the code inside the method createObstacleFile()
    # BSD 3-Clause License

    # Copyright(c) 2020, Francesco Verdoja
    # All rights reserved.

    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:

    # 1. Redistributions of source code must retain the above copyright notice, this
    # list of conditions and the following disclaimer.

    # 2. Redistributions in binary form must reproduce the above copyright notice,
    # this list of conditions and the following disclaimer in the documentation
    # and/or other materials provided with the distribution.

    # 3. Neither the name of the copyright holder nor the names of its
    # contributors may be used to endorse or promote products derived from
    # this software without specific prior written permission.

    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    # FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    # DAMAGES(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    #         SERVICES
    #         LOSS OF USE, DATA, OR PROFITS
    #         OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    # OR TORT(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    # © 2021 GitHub, Inc.
    # Terms
    # Privacy
    # Security
    # Status
    # Docs
