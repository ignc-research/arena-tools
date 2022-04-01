# Create a Gazebo map from the occupancy map
Creating a Gazebo map from the 2D occupancy map, created by *arena-tools* can be broken down into six steps

❶ [Transform the `pgm` file into an `svg`](#1-transform-the-pgm-file-into-an-svg)

❷ [Open the `svg` in Blender](#2-open-the-svg-in-blender)

❸ [Scale and Extrude the `svg`](#3-scale-and-extrude-the-svg)

❹ [Convert to `mesh`](#4-convert-to-mesh)

❺ [(Optinal) simplify the world for higher simulation speed](#5-optinal-simplify-the-world-for-higher-simulation-speed)

❻ [Include the mesh into the world file and save the file](#6-include-the-mesh-into-the-world-file-and-save-the-file)

---

### 1. Transform the `pgm` file into an `svg`
Use *Incspace* to transform the image to an `svg`

### 2. Open the `svg` in Blender
Open *Blender*, clear the scene and import the `svg`
### 3. Scale and Extrude the `svg`
When working with *arena-tools* worlds have a size of 25x25m. You can determine this by multiplying the resolution (pixel per meter) with the number of pixels.

### 4. Convert to `mesh`
Right-click and select, convert to `mesh`

### 5. (Optinal) simplify the world for higher simulation speed
The gazebo simulation-speed can be increased by decreasing the model complexity in this case the number of wires. This can be done with the *decimate* tool. 
> **NOTE**: Don't reduce the number to much, so that structural integrety of the map stays intact 

### 6. Include the mesh into the world file and save the file
Create a new world folder under: <code>simulator_setup/worlds/<var>WORLD_NAME</var></code>. Export the mesh object in `dae` format under the name `map.dae`. Download the `.world` file into that folder. You can run the code below:
<pre class="devsite-click-to-copy">
roscd simulator_setup/worlds/<var>WORLD_NAME</var>
wget https://raw.githubusercontent.com/ignc-research/arena-tools/main/map_to_gazebo/map.world
</pre>
