import json
import os.path

CONFIG_DEFAULT_FILE = "config.json"
CONFIG_DEVELOPMENT_FILE = "config-development.jaon"

def get_config():
    default_config = {"env" : "unknown"}

    return merge_configs(
        default_config,
        parse_config(CONFIG_DEFAULT_FILE),
        parse_config(CONFIG_DEVELOPMENT_FILE)
    )

def parse_config(filename):
    config = {}

    if os.path.isfile(filename):
        f = open(filename, "r")
        config = json.load(f)
        f.close()
    
    return config

def merge_configs(*configs):
    z = {}

    for config in configs:
        z.update(config)
    
    return z