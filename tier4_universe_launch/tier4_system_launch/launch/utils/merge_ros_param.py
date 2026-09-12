# Copyright 2026 TIER IV, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import pathlib
import tempfile

from launch import LaunchContext
from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch.actions import SetLaunchConfiguration
from launch.substitutions import LaunchConfiguration
from launch.utilities import perform_substitutions
import yaml


def load_param_file(path: pathlib.Path):
    with path.open() as fp:
        data = yaml.safe_load(fp)
    # TODO(isamu-takagi): Support any namespace.
    return data["/**"]["ros__parameters"]


def save_param_file(data: dict):
    # TODO(isamu-takagi): Support any namespace.
    data = {"/**": {"ros__parameters": data}}
    with tempfile.NamedTemporaryFile(mode="w", prefix="system_launch_", delete=False) as fp:
        yaml.safe_dump(data, fp)
        return fp.name


def merge_param_dict(x: dict, y: dict):
    same_keys = x.keys() & y.keys()
    result = {key: value for key, value in (x | y).items() if key not in same_keys}
    for key in same_keys:
        result[key] = merge_param_data(x[key], y[key])
    return result


def merge_param_data(x: any, y: any):
    if type(x) is not type(y):
        raise TypeError(f"type mismatch: {type(x)} {type(y)}")
    if type(x) is list:
        return x + y
    if type(x) is dict:
        return merge_param_dict(x, y)
    raise TypeError(f"duplicate parameters: {x} {y}")


def merge_param(params: list[dict]):
    return functools.reduce(merge_param_data, params, {})


def launch_setup(context: LaunchContext):
    paths = perform_substitutions(context, [LaunchConfiguration("paths")])
    paths = yaml.safe_load(paths)
    paths = paths if type(paths) is list else [paths]
    paths = [pathlib.Path(path) for path in paths]
    param = merge_param(load_param_file(path) for path in paths)
    return [SetLaunchConfiguration(LaunchConfiguration("output"), save_param_file(param))]


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=launch_setup)])
