import os
import yaml

# Determine the path to config.yaml relative to this file.
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

with open(CONFIG_PATH, "r") as file:
    CONFIG = yaml.safe_load(file)
