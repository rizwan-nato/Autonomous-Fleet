from time import time

def turn_command(amplitude):
    return (100 * amplitude, -100 * amplitude)


def line_command_old(orientation):
    if orientation is None:
        return (0, 0)
    
    coeff = 82
    correct_threshold = 0
    correction = abs(orientation)
    base_speed = 50 - round(correction * 50)

    #coeff = 50
    #correct_threshold = 0
    #correction = abs(orientation)
    #base_speed = 50 - round(correction * 50)

    if correction < correct_threshold:
        return (base_speed, base_speed)
    elif orientation > 0:
        return (base_speed - round(coeff * correction), base_speed + round(coeff * correction))
    else:
        return (base_speed + round(coeff * correction), base_speed - round(coeff * correction))


last_orientation = 0
last_time = time()


def line_command(orientation):
    global last_orientation, last_time

    if orientation is None:
        return 0, 0

    delta_t = time() - last_time
    last_time = time()

    delta_orientation = orientation - last_orientation
    last_orientation = orientation

    k_p = 85
    k_d = 50
    base_speed = 45 - round(orientation**2 * 60)

    orientation_variation = delta_orientation / delta_t

    command = k_p*orientation + k_d * orientation_variation
    command = round(command)

    motor_speeds = base_speed - command, base_speed + command

    #print("command: {} ; orie: {} ; var: {} ; motor_speed: {}".format(command, orientation, orientation_variation, motor_speeds))

    return motor_speeds

