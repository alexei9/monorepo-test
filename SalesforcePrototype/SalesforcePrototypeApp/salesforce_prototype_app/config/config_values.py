import configparser
import os


def get_config_value(section_name, setting_name):
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'local_only/config.ini'))
    return config[section_name][setting_name]


