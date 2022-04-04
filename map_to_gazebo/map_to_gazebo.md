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


https://user-images.githubusercontent.com/82460419/161525553-3b1c82d1-a3b3-4a16-a0b2-909dcf0a2b1e.mp4


### 2. Open the `svg` in Blender
Open *Blender*, clear the scene and import the `svg`


https://user-images.githubusercontent.com/82460419/161519992-8df523d2-5d58-468a-8290-ed622cd6ab00.mp4



### 3. Scale and Extrude the `svg`
When working with *arena-tools* worlds have a size of 25x25m. You can determine this by multiplying the resolution (pixel per meter) with the number of pixels.


https://user-images.githubusercontent.com/82460419/161520127-88d7a1f9-654a-452d-8154-7809b3952d1d.mp4


### 4. Convert to `mesh`
Right-click and select, convert to `mesh`


https://user-images.githubusercontent.com/82460419/161520173-39376fcb-b115-454c-9b3d-7b1b934e32f3.mp4


### 5. (Optinal) simplify the world for higher simulation speed
The gazebo simulation-speed can be increased by decreasing the model complexity in this case the number of wires. This can be done with the *decimate* tool. 
> **NOTE**: Don't reduce the number to much, so that structural integrety of the map stays intact 


https://user-images.githubusercontent.com/82460419/161522835-be7ad839-f736-4dae-8954-ab7ab5904904.mp4


### 6. Include the mesh into the world file and save the file
Create a new world folder under: <code>simulator_setup/worlds/<var>WORLD_NAME</var></code>. Export the mesh object in `dae` format under the name `map.dae`. Download the `.world` file into that folder. You can run the code below:
<pre class="devsite-click-to-copy">
roscd simulator_setup/worlds/<var>WORLD_NAME</var>
wget https://raw.githubusercontent.com/ignc-research/arena-tools/main/map_to_gazebo/map.world
</pre>


https://user-images.githubusercontent.com/82460419/161523914-8808b4cf-8965-4cf5-96d5-7a45b9d061c1.mp4


