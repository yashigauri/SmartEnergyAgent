
import random

temperature_options   = ["cold", "comfortable", "hot"]
time_options          = ["morning", "afternoon", "night"]
occupancy_options     = ["occupied", "empty"]
price_options = ["cheap", "moderate", "expensive"]


actions = [
    "AC_ON|GEYSER_ON|LIGHTS_ON",
    "AC_ON|GEYSER_ON|LIGHTS_OFF",
    "AC_ON|GEYSER_OFF|LIGHTS_ON",
    "AC_ON|GEYSER_OFF|LIGHTS_OFF",
    "AC_OFF|GEYSER_ON|LIGHTS_ON",
    "AC_OFF|GEYSER_ON|LIGHTS_OFF",
    "AC_OFF|GEYSER_OFF|LIGHTS_ON",
    "AC_OFF|GEYSER_OFF|LIGHTS_OFF",
]


def get_reward(state, action):

    reward = 0

    ac_on     = "AC_ON"     in action
    geyser_on = "GEYSER_ON" in action
    lights_on = "LIGHTS_ON" in action

    if not ac_on and not geyser_on and not lights_on:
        reward += 3

    if lights_on and state["occupancy"] == "occupied":
        reward += 1

    if state["electricity_price"] == "expensive":
        if ac_on or geyser_on:
            reward -= 3

    if ac_on and state["occupancy"] == "empty":
        reward -= 5

    if not ac_on and state["temperature"] == "hot" and state["occupancy"] == "occupied":
        reward -= 6

    return reward

def celsius_to_category(temp_c):
    if temp_c < 20:
        return "cold"
    elif temp_c < 28:
        return "comfortable"
    else:
        return "hot"

def rcwl_to_occupancy(occupied_bool):
    return "occupied" if occupied_bool else "empty"

def get_seasonal_price(hour, month):
    is_summer = 4 <= month <= 9
    is_peak = (7 <= hour < 10) or (18 <= hour < 22)
    is_shoulder = (10 <= hour < 18) or (22 <= hour < 23)
    if is_summer:
        if is_peak:     return "expensive"
        if is_shoulder: return "moderate"
        return "cheap"
    else:
        if is_peak:     return "moderate"
        return "cheap"

def build_state_from_sensors(temp_c, humidity, occupied, now):
    import datetime
    if now is None:
        now = datetime.datetime.now()
    return {
        "temperature":       celsius_to_category(temp_c),
        "time_of_day":       "morning" if 5 <= now.hour < 12 else "afternoon" if now.hour < 20 else "night",
        "occupancy":         rcwl_to_occupancy(occupied),
        "electricity_price": get_seasonal_price(now.hour, now.month),
        "_raw_temp_c":   temp_c,
        "_raw_humidity": humidity,
        "_raw_occupied": occupied,
        "_hour":         now.hour,
        "_month":        now.month,
        "_season":       "summer" if 4 <= now.month <= 9 else "winter",
    }

