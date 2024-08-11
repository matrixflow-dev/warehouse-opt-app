import json
import warnings
from pathlib import Path
from typing import Optional

import numpy as np

from behavior_opt.sh_core.typing import (
    AgentConfig,
    ItemConfig,
    Length,
    MapConfig,
    PickingTask,
    RackConfig,
)

DATASET = "apparel"


def read_map_config(
    map_config_path: Path, stock_items_path: Optional[Path]=None, config_path: Optional[Path]=None
) -> MapConfig:
    if map_config_path.suffix == ".csv":
        assert config_path is not None, "config_path must be specified"
        return read_map_config_csv(map_config_path, config_path)
    elif map_config_path.suffix == ".json":
        return read_map_config_json(map_config_path, stock_items_path)
    else:
        raise ValueError(f"Unknown map config file type: {map_config_path}")


def read_map_config_csv(map_config_path: Path, config_path: Path) -> MapConfig:
    with open(config_path) as f:
        config = json.load(f)
        config = config[DATASET]
    map_width: Length = config["MAP_WIDTH"]
    map_height: Length = config["MAP_HEIGHT"]
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        raw_map_config = np.loadtxt(
            map_config_path, dtype=str, delimiter=",", skiprows=1
        )
    if len(raw_map_config) == 0:
        return MapConfig(map_width=map_width, map_height=map_height, racks=[])
    if raw_map_config.ndim == 1:
        raw_map_config = raw_map_config.reshape(1, -1)

    rack_positions = raw_map_config[:, 1:3].astype(int)
    rack_pick_directions = raw_map_config[:, 4]
    rack_configs: list[RackConfig] = []
    for pos, pick_direction in zip(rack_positions, rack_pick_directions):
        pos = list(pos)
        rack_configs.append(
            RackConfig(width=1, height=1, pos=pos, pick_direction=pick_direction)
        )
    map_config: MapConfig = MapConfig(
        map_width=map_width, map_height=map_height, racks=rack_configs
    )
    return map_config


def read_map_config_json(map_config_path: Path, stock_items_path: Optional[Path]=None) -> MapConfig:
    with open(map_config_path) as f:
        raw_map_config = json.load(f)
    map_width: Length = raw_map_config["map_width"]
    map_height: Length = raw_map_config["map_height"]
    racks: list[RackConfig] = []
    for rack_config in raw_map_config["racks"]:
        racks.append(
            RackConfig(
                width=rack_config["width"],
                height=rack_config["height"],
                # row, col
                pos=[rack_config["pos"][0], rack_config["pos"][1]],
                pick_direction=rack_config["pick_direction"],
            )
        )
    map_config: MapConfig = MapConfig(
        map_width=map_width, map_height=map_height, racks=racks
    )
    if stock_items_path is not None:
        with open(stock_items_path) as f:
            stock_items = json.load(f)
    else:
        stock_items = raw_map_config
    item_configs: list[ItemConfig] = [
    ItemConfig(
        name=item["name"],
        pos=[int(item["pos"][0]), int(item["pos"][1])],
        amount=int(item["volume"]),
        volume=1,
    )
    for item in stock_items["items"]
]
    return map_config, item_configs


def read_picking_list(picking_list_path: Path) -> list[PickingTask]:
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        picking_list = np.loadtxt(
            picking_list_path, dtype=str, delimiter=",", skiprows=1
        )
    if len(picking_list) == 0:
        return []
    if picking_list.ndim == 1:
        picking_list = picking_list.reshape(1, -1)
    picking_list = list(
        map(
            lambda x: PickingTask(
                name=x[0], pos=[int(x[2]), int(x[3])], amount=int(x[1])
            ),
            picking_list,
        )
    )
    return picking_list


def read_agent_config(agents_path: Path) -> list[AgentConfig]:
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        agents = np.loadtxt(agents_path, dtype=str, delimiter=",", skiprows=1)
    assert len(agents) > 0, "No agent config found"
    if agents.ndim == 1:
        agents = agents.reshape(1, -1)
    agent_configs: list[AgentConfig] = [
        AgentConfig(
            name=agent[0],
            capacity=int(agent[1]),
            pos=[int(agent[2]), int(agent[3])],
        )
        for agent in agents
    ]
    return agent_configs


def read_item_config(items_path: Path) -> list[ItemConfig]:
    # [
    #     "item_id",
    #     "separated",
    #     "stored_amount",
    #     "weight",
    #     "zone",
    #     "cap_remain",
    #     "ship_place_row",
    #     "ship_place_col",
    #     "store_place_row",
    #     "store_place_col",
    #     "predict_ship_amount",
    #     "predict_ship_frequency",
    # ]
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        raw_items = np.loadtxt(items_path, dtype=str, delimiter=",", skiprows=1)
    if len(raw_items) == 0:
        return []
    if raw_items.ndim == 1:
        raw_items = raw_items.reshape(1, -1)
    item_configs: list[ItemConfig] = [
        ItemConfig(
            name=item[0],
            pos=[int(item[8]), int(item[9])],
            amount=int(item[2]),
            volume=int(item[3]),
        )
        for item in raw_items
    ]
    return item_configs
