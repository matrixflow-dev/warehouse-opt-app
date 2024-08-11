import argparse
import json
import os
import random
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from behavior_opt.mca.planning import behavior_opt
from behavior_opt.mca.postprocess import postprocess
from behavior_opt.mca.preprocess import preprocess
from behavior_opt.sh_core import Position
from behavior_opt.sh_core.typing import MapConfig
from behavior_opt.utils.file_io import read_map_config


class AgentNumRange(NamedTuple):
    min: int
    max: int

    def get_agent_num_list(self) -> list[int]:
        return list(range(self.min, self.max + 1))


class AgentPosRange:
    def __init__(self, left_top: Position, right_bottom: Position) -> None:
        if left_top.row > right_bottom.row:
            raise ValueError("left_top.row must be less than right_bottom.row")
        if left_top.col > right_bottom.col:
            raise ValueError("left_top.col must be less than right_bottom.col")
        if left_top.row == right_bottom.row and left_top.col == right_bottom.col:
            raise ValueError("left_top and right_bottom cannot be the same")
        self.left_top = left_top
        self.right_bottom = right_bottom

    def get_agent_positions(self, n_agents: int) -> list[Position]:
        """範囲内にあるエージェントの位置をランダムに人数分返す"""
        position_list = [
            Position(row, col)
            for row in range(self.left_top.row, self.right_bottom.row + 1)
            for col in range(self.left_top.col, self.right_bottom.col + 1)
        ]
        return random.sample(position_list, n_agents)

    def is_stuff_in_range(self, pos: Position) -> bool:
        return (
            self.left_top.row <= pos.row < self.right_bottom.row
            and self.left_top.col <= pos.col < self.right_bottom.col
        )


def create_agent_csv(
    map_config: MapConfig,
    agents_dir: Path,
    agent_num_range: AgentNumRange,
    agent_capacity: int,
) -> None:
    map_width = map_config["map_width"]
    map_height = map_config["map_height"]
    agent_pos_range = AgentPosRange(
        Position(map_height - 1, 0),
        Position(map_height - 1, map_width - 2),
    )
    os.makedirs(agents_dir, exist_ok=True)
    n_agents_list = agent_num_range.get_agent_num_list()
    for n_agents in n_agents_list:
        agent_pos_list = agent_pos_range.get_agent_positions(n_agents)
        agent_path = agents_dir / f"agents{n_agents}.csv"
        with open(agent_path, "w") as f:
            print("agent_id,amount,initial_place_row,initial_place_col", file=f)
            for i, pos in enumerate(agent_pos_list):
                print(f"{i},{agent_capacity},{pos.row},{pos.col}", file=f)


def set_random_pos(map_config: MapConfig) -> Position:
    rack = random.choice(map_config["racks"])
    if rack["pick_direction"] == "horizontal":
        pos_0 = random.randint(rack["pos"][0], rack["pos"][0] + rack["height"] - 1)
        pos = Position(pos_0, rack["pos"][1])
    elif rack["pick_direction"] == "vertical":
        pos_1 = random.randint(rack["pos"][1], rack["pos"][1] + rack["width"] - 1)
        pos = Position(rack["pos"][0], pos_1)
    else:
        raise ValueError("pick_direction must be horizontal or vertical")
    return pos


def create_item_config(map_config: MapConfig, n_items: int) -> list[dict[str, Any]]:
    item_configs: list[dict[str, Any]] = []
    for i in range(n_items):
        pos = set_random_pos(map_config)
        item_config = {}
        item_config["item_id"] = str(i)
        item_config["separated"] = "merged"
        item_config["stored_amount"] = 100
        item_config["weight"] = 1
        item_config["zone"] = 1
        item_config["cap_remain"] = 100
        item_config["ship_place_row"] = map_config["map_height"] - 1
        item_config["ship_place_col"] = map_config["map_width"] - 1
        item_config["store_place_row"] = pos.row
        item_config["store_place_col"] = pos.col
        item_config["predict_ship_amount"] = 0
        item_config["predict_ship_frequency"] = 0
        item_configs.append(item_config)
    return item_configs


def create_picking_list(item_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picking_list: list[dict[str, Any]] = []
    for item_config in item_configs:
        picking_list.append(
            {
                "item_id": item_config["item_id"],
                "amount": 1,
                "ship_place_row": item_config["ship_place_row"],
                "ship_place_col": item_config["ship_place_col"],
            }
        )
    return picking_list


def create_item_files(
    map_config: MapConfig, item_config_path: Path, picking_list_path: Path, n_items: int
):
    item_configs = create_item_config(map_config, n_items)
    picking_list = create_picking_list(item_configs)
    pd.DataFrame(item_configs).to_csv(item_config_path, index=False)
    pd.DataFrame(picking_list).to_csv(picking_list_path, index=False)


def optimization(
    input_path: Path,
    output_path: Path,
    agent_num_range: AgentNumRange,
    agent_capacity: int,
    n_items: int,
) -> list[int]:
    agents_dir = input_path / "agents"
    map_config_path = input_path / "map_config.json"
    item_config_path = input_path / "store_info.csv"
    picking_list_path = input_path / "picking_list.csv"
    mca_dir = Path("tmp")
    mca_file_path = mca_dir / "storehouse.out"
    task_file_path = mca_dir / "tasks.csv"
    map_config = read_map_config(map_config_path, stock_items_path="####optimizationを使うなら修正する########")
    create_agent_csv(map_config, agents_dir, agent_num_range, agent_capacity)
    create_item_files(map_config, item_config_path, picking_list_path, n_items)

    step_sum_list: list[int] = []
    for n_agents in agent_num_range.get_agent_num_list():
        agents_path = agents_dir / f"agents{n_agents}.csv"
        output_dir = output_path / f"{n_agents}"
        os.makedirs(output_dir, exist_ok=True)
        preprocess(
            map_config_path,
            None,
            agents_path,
            item_config_path,
            picking_list_path,
            mca_dir,
        )
        behavior_opt(agents_path, mca_dir)
        path_output = postprocess(
            task_file_path, agents_path, mca_file_path, output_dir
        )
        step_sum_list.append(sum(map(lambda x: len(x), path_output)))
    return step_sum_list


def save_step_list(step_list: list[int], output_path: Path):
    with open(output_path / "all_steps.txt", "w") as f:
        print(",".join(map(str, step_list)), file=f)


def main():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="agents_opt.py")
    parser.add_argument("-i", "--input", required=True, type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("-n", "--n_items", required=True, type=int)
    parser.add_argument("-a", "--agent_num", required=True, type=int)
    args = parser.parse_args()
    input_path: Path = args.input
    output_path: Path = args.output
    n_items = args.n_items
    agent_num = args.agent_num
    agent_num_range = AgentNumRange(1, agent_num)
    step_list = optimization(
        input_path,
        output_path,
        agent_num_range,
        5,
        n_items,
    )
    save_step_list(step_list, output_path)
