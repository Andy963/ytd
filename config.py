# ！/usr/bin/env python
# encoding:utf-8
# Created by Andy at 2022/4/4
import json

from logger import FileSplitLogger


def read_config(file_type='json', file_name='./config.json'):
    """
    Func:read config
    Args:None
    Example:
    Return: None
    """
    with open(file_name, 'r') as f:
        if file_type == 'json':
            return json.load(f)
        elif file_type == 'yaml':
            return yaml.load(f)
        return None


config = read_config()
fl = FileSplitLogger(f"{config['log_path']}/ytd.log")
log = fl.logger