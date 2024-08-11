import networkx as nx
from networkx import Graph
from dataclasses import dataclass
from copy import deepcopy
from behavior_opt.a_star.task_assignment import ManuallyTaskAssignment
from behavior_opt.sh_core import World, Task, Item, StorePoint, Objective
from pathlib import Path
from behavior_opt.utils.file_io import (
    read_agent_config,
    read_item_config,
    read_map_config,
    read_picking_list,
)
import csv
import argparse
import time


def create_graph(map_):
    G: Graph = nx.grid_2d_graph(map_.shape[0], map_.shape[1])
    for i in range(map_.shape[0]):
        for j in range(map_.shape[1]):
            if map_[i, j] == 1:
                G.remove_node((i, j))  # type: ignore
    return G


@dataclass
class Output:
    path: list
    action: Objective
    item: Item


def read_task_assignment(file_path: str, world: World):
    with open(file_path, "r") as f:
        lines = f.readlines()
    agent_list = []
    task_list = []
    action_list = []
    for line in lines[1:]:
        agent_id, item_name, row, col, action = line.strip().split(",")
        agent_list.append(agent_id)
        items = deepcopy(world.items)
        item = items.pop(item_name)

        task_list.append(world.tasks[item])
        if action == "PICK_UP":
            action = Objective.PICK_UP
        elif action == "DOCK":
            action = Objective.DOCK
        elif action == "DROP_OFF":
            action = Objective.DROP_OFF
        action_list.append(action)
    return agent_list, task_list, action_list


def write_output_csv(file_path: str, result: dict):
    max_step = max(map(len, [i["path"] for i in result.values()]))

    with open(file_path, "w") as f:
        writer = csv.writer(f)
        # step,0134_path_row,0134_path_col,0134_pick_up,0134_drop_off
        writer.writerow(
            ["step"]
            + [
                f"{i}_{suffix}"
                for i in result.keys()
                for suffix in ["path_row", "path_col", "pick_up", "drop_off"]
            ]
        )
        memory_path = {i: [0, 0] for i in result.keys()}
        for i in range(max_step):
            row = [i]

            for agent_name, value in result.items():
                if i < len(value["path"]):
                    row.extend(
                        [
                            value["path"][i][0],
                            value["path"][i][1],
                            value["pickup"][i],
                            value["dropoff"][i],
                        ]
                    )
                    memory_path[agent_name] = value["path"][i]
                else:
                    row.extend(
                        [
                            memory_path[agent_name][0],
                            memory_path[agent_name][1],
                            "",
                            "",
                        ]
                    )
            writer.writerow(row)


def planning(
    config_path: Path,
    map_config_path: Path,
    agent_config_path: Path,
    item_config_path: Path,
    picking_list_path: Path,
    task_assignment_path: Path,
):
    if config_path is None or item_config_path is None:
        # map_config_pathはjsonのみ
        assert map_config_path.suffix == ".json"
        map_config, item_config = read_map_config(map_config_path)
    else:
        map_config = read_map_config(map_config_path, config_path)
        item_config = read_item_config(item_config_path)
    agent_config = read_agent_config(agent_config_path)
    picking_list = read_picking_list(picking_list_path)

    world = World(
        map_config=map_config,
        picking_list=picking_list,
        agent_configs=agent_config,
        item_configs=item_config,
    )
    copy_world = deepcopy(world)
    agent_list, task_list, action_list = read_task_assignment(
        task_assignment_path, copy_world
    )
    current_agents = copy_world.agents
    plain_map = copy_world.plain_map
    graph_map = create_graph(plain_map)
    task_assignment = ManuallyTaskAssignment(copy_world)
    task_assignment.assign(agent_list, task_list, action_list)
    action_output = {i.name: [] for i in world.agents}
    while True:
        for agent_id, agent in enumerate(current_agents):
            actions = task_assignment.actions[agent.name]
            if len(actions) == 1 and agent.pos == agent.goal.pos:
                del task_assignment.actions[agent.name]
                del task_assignment.assigned_tasks[agent.name]
                current_agents.remove(agent)
        if len(current_agents) == 0:
            break
        task_assignment.set_target()

        for agent_id, agent in enumerate(current_agents):
            start = agent.pos
            target = agent.target
            path = nx.shortest_path(graph_map, tuple(start), tuple(target))
            agent.pos = target
            agent.target = None
            if task_assignment.current_task[agent.name] is None:
                item = None
            else:
                item = task_assignment.current_task[agent.name].item
            assert (
                path[0] == action_output[agent.name][-1].path[-1]
                if action_output[agent.name]
                else agent.pos
            ), path
            output = Output(
                path=path,
                action=task_assignment.current_action[agent.name],
                item=item,
            )
            action_output[agent.name].append(output)
    result = {agent.name: None for agent in world.agents}
    for agent_id, agent in enumerate(world.agents):
        output_list = action_output[agent.name]
        all_path = [output_list[0].path[0]]
        pickup_list = [""]
        dropoff_list = [""]
        for output in output_list:
            assert output.path[0] == all_path[-1], f"{output.path} != {all_path}"
            tmp_path = output.path[1:]
            all_path.extend(tmp_path)
            if output.action == Objective.PICK_UP:
                if len(tmp_path) == 0:
                    pickup_list[-1] = pickup_list[-1] + " " + output.item.name
                else:
                    pickup_list += [""] * (len(tmp_path) - 1)
                    pickup_list.append(output.item.name)
                    dropoff_list += [""] * len(tmp_path)
            elif output.action == Objective.DROP_OFF:
                if len(tmp_path) == 0:
                    dropoff_list[-1] = dropoff_list[-1] + " " + output.item.name
                else:
                    dropoff_list += [""] * (len(tmp_path) - 1)
                    dropoff_list.append(output.item.name)
                    pickup_list += [""] * len(tmp_path)
            elif output.action == Objective.DOCK:
                pickup_list += [""] * len(tmp_path)
                dropoff_list += [""] * len(tmp_path)
        result[agent.name] = {
            "path": all_path,
            "pickup": pickup_list,
            "dropoff": dropoff_list,
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="mca.py")
    parser.add_argument("-a", "--agent-config-path", required=True, type=Path)
    parser.add_argument("-i", "--item-config-path", required=False, type=Path)
    parser.add_argument("-m", "--map-config-path", required=True, type=Path)
    parser.add_argument("-c", "--config-path", required=False, type=Path)
    parser.add_argument("-p", "--picking-list-path", required=True, type=Path)
    parser.add_argument("-ta", "--task-assignment-path", required=True, type=Path)
    parser.add_argument("-o", "--output-dir", required=True, type=Path)
    args = parser.parse_args()
    map_config_path: Path = args.map_config_path
    config_path = args.config_path
    agent_config_path: Path = args.agent_config_path
    item_config_path = args.item_config_path
    picking_list_path: Path = args.picking_list_path
    task_assignment_path: Path = args.task_assignment_path
    output_dir_path: Path = args.output_dir

    output_dir_path.mkdir(exist_ok=True, parents=True)
    start_time = time.time()
    result = planning(
        config_path,
        map_config_path,
        agent_config_path,
        item_config_path,
        picking_list_path,
        task_assignment_path,
    )

    write_output_csv(output_dir_path / "output.csv", result)

    elapsed_time = time.time() - start_time
    makespan = max(map(lambda x: len(x), [i["path"] for i in result.values()]))
    avg_steps = sum(map(lambda x: len(x), [i["path"] for i in result.values()])) / len(
        result
    )
    print(f"elapsed_time:{elapsed_time}")
    print(f"makespan:{makespan}")
    print(f"avg steps:{avg_steps}")
    for i, path in enumerate([i["path"] for i in result.values()]):
        print(f"agent:{i} steps:{len(path)}")
