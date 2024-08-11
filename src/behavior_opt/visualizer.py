import argparse
import json
import warnings
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from behavior_opt.sh_core import AgentConfig, MapConfig, Position
from behavior_opt.sh_core.typing import ItemConfig, Name, PickingTask
from behavior_opt.sh_core.world import World
from behavior_opt.storehouse import raw_env
from behavior_opt.utils.file_io import (
    read_agent_config,
    read_item_config,
    read_map_config,
    read_picking_list,
)


def read_output(
    output_path: Path,
) -> list[dict[str, deque[Position] | deque[Name]]]:
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        output = np.loadtxt(output_path, dtype=str, delimiter=",", skiprows=1)
    if output.size == 0:
        return []

    if output.ndim == 1:
        output = output.reshape(1, -1)
    output_list: list[dict[str, deque[Position] | deque[str]]] = []
    num_agent = (output.shape[1] - 1) // 4
    for i in range(num_agent):
        path = deque(
            map(
                lambda x: Position(int(x[0]), int(x[1])),
                output[:, 1 + 4 * i : 3 + 4 * i],
            )
        )
        pick_up = deque(map(lambda x: x.rstrip().split(" "), output[:, 3 + 4 * i]))
        drop_off = deque(map(lambda x: x.rstrip().split(" "), output[:, 4 + 4 * i]))
        output_list.append({"path": path, "pick_up": pick_up, "drop_off": drop_off})
    return output_list


def create_image(
    map_config: MapConfig,
    picking_list: list[PickingTask],
    agent_configs: list[AgentConfig],
    item_configs: list[ItemConfig],
    behavior_opt_output: list[dict[str, deque[Position] | deque[Name]]],
    output_gif_path: Path,
) -> None:
    world = World(
        map_config=map_config,
        item_configs=item_configs,
        picking_list=picking_list,
        agent_configs=agent_configs,
    )
    env = raw_env(world=world, output_list=behavior_opt_output)
    env.reset()
    frame_list: list[Image.Image] = []
    for i, _ in enumerate(env.agent_iter()):  # type: ignore
        _, _, done, _ = env.last()  # type: ignore
        if done:
            action = None
        else:
            action = 0
        env.step(action)
        if i % len(env.possible_agents) == 0:
            frame_list.append(Image.fromarray(env.render(mode="rgb_array")))  # type: ignore
    frame_list[0].save(
        output_gif_path,
        save_all=True,
        append_images=frame_list[1:],
        duration=2,
        loop=0,
    )


def visualizer(
    map_config_path: Path,
    stock_items_path: Path | None,
    config_path: Path | None,
    item_configs_path: Path | None,
    agent_configs_path: Path,
    picking_list_path: Path,
    behavior_opt_output_path: Path,
    output_gif_path: Path,
) -> None:
    if config_path is None or item_configs_path is None:
        assert map_config_path.suffix == ".json", "map_config_path must be a json file"
        map_config, item_config = read_map_config(map_config_path, stock_items_path=stock_items_path)
    else:
        map_config = read_map_config(map_config_path, config_path)
        item_config = read_item_config(item_configs_path)
    picking_list = read_picking_list(picking_list_path)
    agent_config = read_agent_config(agent_configs_path)
    behavior_opt_output = read_output(behavior_opt_output_path)
    if behavior_opt_output:
        create_image(
            map_config=map_config,
            picking_list=picking_list,
            agent_configs=agent_config,
            item_configs=item_config,
            behavior_opt_output=behavior_opt_output,
            output_gif_path=output_gif_path,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="visualizer.py")
    parser.add_argument("-a", "--agent-configs-path", required=True, type=Path)
    parser.add_argument("-i", "--item-configs-path", required=False, type=Path)
    parser.add_argument("-m", "--map-config-path", required=True, type=Path)
    parser.add_argument("-s", "--stock-items-path", required=True, type=Path)
    parser.add_argument("-c", "--config-path", required=False, type=Path)
    parser.add_argument("-p", "--picking-list-path", required=True, type=Path)
    parser.add_argument("-B", "--behavior-opt-output-path", required=True, type=Path)
    parser.add_argument("-o", "--output-gif-path", required=True, type=Path)
    args = parser.parse_args()
    map_config_path: Path = args.map_config_path
    stock_items_path: Path = args.stock_items_path
    config_path = args.config_path
    agent_configs_path: Path = args.agent_configs_path
    item_configs_path = args.item_configs_path
    picking_list_path: Path = args.picking_list_path
    behavior_opt_output_path: Path = args.behavior_opt_output_path
    output_gif_path = args.output_gif_path
    output_gif_path.parent.mkdir(exist_ok=True, parents=True)
    visualizer(
        map_config_path=map_config_path,
        stock_items_path=stock_items_path,
        config_path=config_path,
        agent_configs_path=agent_configs_path,
        item_configs_path=item_configs_path,
        picking_list_path=picking_list_path,
        behavior_opt_output_path=behavior_opt_output_path,
        output_gif_path=output_gif_path,
    )
