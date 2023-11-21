#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date     : 2023/11/21
# @FileName : config.py
# Created by; Andy
from pathlib import Path

import yaml

p = Path('/etc/ytd/config.yaml')
with open(p, 'r') as f:
    config_yaml = yaml.safe_load(f)

api_id = config_yaml.get('api_id')
api_hash = config_yaml.get('api_hash')
token = config_yaml.get('token')
download_path = config_yaml.get('download_path')