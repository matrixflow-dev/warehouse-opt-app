import argparse
from copy import deepcopy
from pathlib import Path

import numpy as np

from behavior_opt.a_star.push_and_swap import Plan_t, PushAndSwap
from behavior_opt.a_star.task_assignment import NearestTaskAssignment
from behavior_opt.sh_core import World, Objective
from behavior_opt.utils.file_io import (
    read_agent_config,
    read_item_config,
    read_map_config,
    read_picking_list,
)


def format_result(
    result: list[Plan_t], current_agents, agents, first_positions
) -> list[list[str]]:
    result = np.array(result)
    result = np.array(list(map(lambda x: x.ravel(), result)))
    solution = np.repeat([np.array(first_positions).ravel()], len(result), axis=0)
    current_agents_names = list(map(lambda x: x.name, current_agents))
    j = 0
    for i, a in enumerate(agents):
        if a.name in current_agents_names:
            solution[:, 2 * i] = result[:, 2 * j]
            solution[:, 2 * i + 1] = result[:, 2 * j + 1]
            j += 1
    return solution


def write_output_csv(
    dir_path: Path,
    output: list[list[int]],
    action_steps_output,
    task_assignment,
    agents,
) -> None:
    output = np.array(output, dtype=object)
    csv_path = dir_path / "output.csv"
    header: list[str] = ["steps"]
    for a in agents:
        agent_name: str = a.name
        header += [
            agent_name + "_path_row",
            agent_name + "_path_col",
            agent_name + "_pick_up",
            agent_name + "_drop_off",
        ]

    for agent_id, a in enumerate(agents):
        action_tasks_list = np.full((2, len(output)), "", dtype=object)
        assigened_tasks = task_assignment.assigned_tasks[a.name]
        actions = task_assignment.actions[a.name]
        steps = action_steps_output[agent_id]
        for i, (action, step) in enumerate(zip(actions, steps)):
            if action == Objective.PICK_UP:
                action_tasks_list[0, step] += assigened_tasks[i].item.name + " "
            elif action == Objective.DROP_OFF:
                action_tasks_list[1, step] += assigened_tasks[i].item.name + " "

        output = np.insert(output, 2 + 4 * agent_id, action_tasks_list, axis=1)
    steps = np.arange(1, len(output) + 1)
    output = np.insert(output, 0, steps, axis=1)
    np.savetxt(
        csv_path,
        output,
        delimiter=",",
        fmt="%s",
        header=",".join(header),
        comments="",
    )


def check_invaild_move(result, first_positions):
    assert (result[0] == first_positions).all(), "first position is not same"
    if len(result) > 1:
        result_diff = np.diff(result, axis=0)
        assert (np.abs(result_diff) <= 1).all(), "Invalid move"


def planning(
    config_path: Path,
    map_config_path: Path,
    agent_config_path: Path,
    item_config_path: Path,
    picking_list_path: Path,
    output_dir: Path,
):
    map_config = read_map_config(map_config_path, config_path)
    picking_list = read_picking_list(picking_list_path)
    agent_configs = read_agent_config(agent_config_path)
    item_configs = read_item_config(item_config_path)
    world = World(
        map_config=map_config,
        item_configs=item_configs,
        agent_configs=agent_configs,
        picking_list=picking_list,
    )
    current_agents = world.agents
    copy_agents = deepcopy(current_agents)
    plain_map = world.plain_map
    task_assignment = NearestTaskAssignment(world)
    task_assignment.assign()
    copy_task_assignment = deepcopy(task_assignment)
    first_positions = np.array([agent.pos for agent in world.agents]).ravel()
    output = np.array(first_positions).ravel()
    action_output = [[] for _ in range(len(world.agents))]
    while True:
        print(f"####{sum(map(len, task_assignment.assigned_tasks))}####")
        for agent_id, agent in enumerate(current_agents):
            actions = task_assignment.actions[agent.name]
            if len(actions) == 1 and agent.pos == agent.goal.pos:
                del task_assignment.actions[agent.name]
                del task_assignment.assigned_tasks[agent.name]
                current_agents.remove(agent)
        if len(current_agents) == 0:
            break
        task_assignment.set_target()
        push_and_swap = PushAndSwap(current_agents, plain_map)
        result, finished_agents = push_and_swap.run()
        assert result is not None, "result is None"
        last_positions: Plan_t = result[-1]
        for agent_id, agent in enumerate(current_agents):
            agent.pos = last_positions[agent_id]
            other_agent_pos = [
                pos for i, pos in enumerate(last_positions) if agent_id != i
            ]
            assert agent.pos not in other_agent_pos, f"{agent.pos} {other_agent_pos}"
        result = format_result(result, current_agents, copy_agents, first_positions)
        check_invaild_move(result, first_positions)
        first_positions = result[-1].copy()
        output = np.vstack([output, result[1:]])
        for agent_id, agent in enumerate(current_agents):
            if agent_id in finished_agents:
                idx = copy_agents.index(agent.name)
                action_output[idx].append(len(output) - 1)

    print(output)
    print("makespan:", len(output))
    write_output_csv(
        output_dir, output, action_output, copy_task_assignment, copy_agents
    )

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="preprocess.py")
    parser.add_argument("-a", "--agent-config-path", required=True, type=Path)
    parser.add_argument("-i", "--item-config-path", required=True, type=Path)
    parser.add_argument("-m", "--map-config-path", required=True, type=Path)
    parser.add_argument("-c", "--config-path", required=True, type=Path)
    parser.add_argument("-p", "--picking-list-path", required=True, type=Path)
    parser.add_argument("-o", "--output-dir", required=True, type=Path)
    args = parser.parse_args()
    map_config_path: Path = args.map_config_path
    config_path = args.config_path
    agent_config_path: Path = args.agent_config_path
    item_config_path = args.item_config_path
    picking_list_path: Path = args.picking_list_path
    output_dir: Path = args.output_dir
    planning(
        config_path=config_path,
        map_config_path=map_config_path,
        agent_config_path=agent_config_path,
        item_config_path=item_config_path,
        picking_list_path=picking_list_path,
        output_dir=output_dir,
    )
