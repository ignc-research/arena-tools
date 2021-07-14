
def get_ros_package_path(package_name: str) -> str:
    try:
        import rospkg
        rospack = rospkg.RosPack()
        return rospack.get_path(package_name)
    except:
        return ""
