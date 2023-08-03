#!/usr/bin/python
# coding:utf-8

from pathlib import Path

import yaml

# config_dir = Path(__file__).parent.parent.resolve() / "config"
config_dir = Path("/etc/ytd")
# load yaml config
with open(config_dir / "config.yml", "r") as f:
    config_yaml = yaml.safe_load(f)


api_id = config_yaml.get("api_id")
api_hash = config_yaml.get("api_hash")
telegram_token = config_yaml.get("token")
download_path = config_yaml.get("download_path")
allowed_telegram_usernames = config_yaml.get("allowed_telegram_usernames", [])
