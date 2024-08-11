import argparse
from pathlib import Path

import numpy as np

from behavior_opt.sh_core import Tasks, World
from behavior_opt.utils.file_io import (
    read_agent_config,
    read_item_config,
    read_map_config,
    read_picking_list,
)

TIMEOUT_MAX = 5000


# mapの作成
def _create_map(world: World, output_dir: Path) -> None:
    file_path = output_dir / "storehouse.map"
    with open(file_path, "w") as f:
        print(f"{world.map_height+2},{world.map_width+2}", file=f)
        print(f"{len(world.end_points)}", file=f)
        print(f"{world.n_agents}", file=f)
        print(f"{TIMEOUT_MAX}", file=f)
        print("@" * (world.map_width + 2), file=f)
        for row in world.world_map:
            field_row = []
            for loc in row:
                if loc == 0:
                    field_type = "."
                elif loc == 1 or loc == 5:
                    field_type = "@"
                elif loc == 4:
                    field_type = "r"
                elif loc == 6:
                    field_type = "e"
                else:
                    field_type = "."
                field_row.append(field_type)
            print("@" + "".join(field_row) + "@", file=f)
        print("@" * (world.map_width + 2), file=f)


# item-storepoint-endpointをつなげる
def _create_task(world: World, output_dir: Path):
    tasks = world.tasks
    # MCA-RMCAのタスクファイルの形式に合わせる
    create_mca_task_file(tasks, output_dir)
    # postprocessのためのタスクファイルを作成
    create_postprocess_task_file(tasks, output_dir)


def create_postprocess_task_file(tasks: Tasks, output_dir: Path):
    # postprocessのためのタスクファイルを作成
    tasks = [
        [task[0].name, task[0].pos[0], task[0].pos[1], task[1].pos[0], task[1].pos[0]]
        for task in tasks
    ]
    header = [
        "item",
        "initial_place_row",
        "initial_place_col",
        "ship_place_row",
        "ship_place_col",
    ]
    np.savetxt(
        output_dir / "tasks.csv",
        tasks,
        fmt="%s",
        delimiter=",",
        header=",".join(header),
        comments="",
    )


def create_mca_task_file(tasks: Tasks, output_dir: Path):
    # MCA-RMCAのタスクファイルの形式に合わせる
    file_path = output_dir / "storehouse.task"
    with open(file_path, "w") as f:
        print(f"{len(tasks)}", file=f)
        for task in tasks:
            print(
                0,
                task[0].end_point.name,
                task[1].end_point.name,
                0,
                0,
                task[0].volume,
                sep="\t",
                file=f,
            )


def preprocess(
    map_config_path: Path,
    config_path: Path | None,
    agent_config_path: Path,
    item_config_path: Path | None,
    picking_list_path: Path,
    output_dir: Path,
):
    if config_path is None or item_config_path is None:
        # map_config_pathはjsonのみ
        assert map_config_path.suffix == ".json"
        map_config, item_config = read_map_config(map_config_path)
    else:
        map_config = read_map_config(map_config_path, config_path)
        item_config = read_item_config(item_config_path)
    picking_list = read_picking_list(picking_list_path)
    agent_config = read_agent_config(agent_config_path)
    world = World(
        map_config=map_config,
        picking_list=picking_list,
        agent_configs=agent_config,
        item_configs=item_config,
    )
    output_dir.mkdir(exist_ok=True, parents=True)
    output_dir.mkdir(exist_ok=True, parents=True)
    _create_map(world, output_dir)
    _create_task(world, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="preprocess.py")
    parser.add_argument("-a", "--agent-config-path", required=True, type=Path)
    parser.add_argument("-i", "--item-config-path", required=False, type=Path)
    parser.add_argument("-m", "--map-config-path", required=True, type=Path)
    parser.add_argument("-c", "--config-path", required=False, type=Path)
    parser.add_argument("-p", "--picking-list-path", required=True, type=Path)
    parser.add_argument("-MD", "--mca-output-dir", required=True, type=Path)
    args = parser.parse_args()
    map_config_path: Path = args.map_config_path
    config_path = args.config_path
    agent_config_path: Path = args.agent_config_path
    item_config_path = args.item_config_path
    picking_list_path: Path = args.picking_list_path
    output_dir: Path = args.mca_output_dir
    preprocess(
        map_config_path=map_config_path,
        agent_config_path=agent_config_path,
        item_config_path=item_config_path,
        picking_list_path=picking_list_path,
        output_dir=output_dir,
        config_path=config_path,
    )

