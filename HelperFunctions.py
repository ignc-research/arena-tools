def get_ros_package_path(package_name: str) -> str:
    try:
        import rospkg
        rospack = rospkg.RosPack()
        return rospack.get_path(package_name)
    except:
        return ""

def get_nth_decimal_part(x: float, n: int) -> int:
    '''
    Get the n'th decimal part of a decimal number.
    Example:
        get_nth_decimal_part(1.234, 2) == 3
    '''
    x *= 10 ** n  # push relevant part directly in front of decimal point
    x %= 10  # remove parts left of the relevant part
    return int(x)  # remove decimal places

def round_one_and_half_decimal_places(x: float) -> float:
    '''
    Round to X.X0 or X.X5.
    Example:
        round_one_and_half_decimal_places(1.234) == 1.25
    '''
    x = round(x, 2)
    y = get_nth_decimal_part(x, 2)
    if y in [1, 2, 8, 9]:
        # normal round
        return round(x, 1)
    elif y in [3, 4]:
        # round up to next 0.05 step
        return round(x, 1) + 0.05
    elif y in [6, 7]:
        # round down to previous 0.05 step
        return round(x, 1) - 0.05
    else:
        # x is X.X0 or X.X5 already
        return x

def normalize_angle(angle: float) -> float:
    import math
    # make sure angle is positive
    while angle < 0:
        angle += 2 * math.pi
    # make sure angle is between 0 and 2 * pi
    angle = math.fmod(angle, 2 * math.pi)
    return angle
    
def get_current_user_path(path_in: str) -> str:
    '''
    Convert a path from another user to the current user, for example:
    "/home/alice/catkin_ws" -> "/home/bob/catkin_ws"
    '''
    if path_in == "":
        return ""
    from pathlib import Path
    path = Path(path_in)
    new_path = Path.home().joinpath(*path.parts[3:])
    return str(new_path)
