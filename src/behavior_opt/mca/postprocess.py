import argparse
import re
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from behavior_opt.sh_core import AgentConfig, Position, Objective
from behavior_opt.utils.file_io import read_agent_config


@dataclass
class TaskAssignmentDetails:
    task_name: str
    task_item_pos: Optional[Position]
    task_ship_pos: Optional[Position]
    task_id: int
    end_point_pos: Position
    ideal_step: int
    real_step: int
    delay: int
    objective: Objective
    release_time: int


def _read_mca_output(file_path: Path) -> tuple[list[str], list[str]]:
    with open(file_path, "r") as f:
        lines = f.readlines()
    # 読み込んだ出力を変形する
    ta_i, path_i = None, None
    for i, line in enumerate(lines):
        if line.startswith("task_assignment:"):
            ta_i = i
        if line.startswith("path_for_each_agent:"):
            path_i = i
            break
    assert (
        ta_i is not None and path_i is not None
    ), "Task assignment or path is not found."
    n_agent = path_i - ta_i - 1
    task_assignment = lines[ta_i + 1 : ta_i + n_agent + 1]
    path_for_each_agent = lines[path_i + 1 : path_i + n_agent + 1]
    return task_assignment, path_for_each_agent


def _read_task(file_path: Path) -> NDArray[np.str_]:
    with warnings.catch_warnings():
        # dismiss empty line warning
        warnings.simplefilter("ignore")
        tasks = np.loadtxt(file_path, dtype=object, delimiter=",", skiprows=1)
    if tasks.ndim == 1:
        tasks = tasks.reshape(1, -1)
    return tasks


def _format_TA_output(
    task_assignment: list[str], tasks: list[list[str]]
) -> list[list[TaskAssignmentDetails]]:
    task_regex = re.compile(
        r"<(\d+)\((\d+)\),(-?\d+),\((\d+),(\d+)\),delay(\d+),act(\d+),r(\d+)>"
    )
    task_assignment_lists: list[TaskAssignmentDetails] = []
    for ta in task_assignment:
        ms = re.findall(task_regex, ta)
        task_assignment_list = []
        for m in ms:
            m = list(map(lambda x: int(x), m))
            ta_output = TaskAssignmentDetails(
                ideal_step=m[0],
                real_step=m[1],
                task_id=m[2],
                task_name=tasks[m[2]][0] if m[2] >= 0 else "",
                task_item_pos=(int(tasks[m[2]][1]), int(tasks[m[2]][2]))
                if m[2] >= 0
                else None,
                task_ship_pos=(int(tasks[m[2]][3]), int(tasks[m[2]][4]))
                if m[2] >= 0
                else None,
                end_point_pos=(m[3] - 2, m[4] - 2),
                delay=m[5],
                objective=Objective(m[6]),
                release_time=m[7],
            )
            task_assignment_list.append(ta_output)
        task_assignment_lists.append(task_assignment_list)

    return task_assignment_lists


def _format_path_output(path_for_each_agent: list[str]) -> list[list[Position]]:
    path_regex = re.compile(r"(\d+)\((\d+),(\d+)\)")
    path_lists = []
    for i, path in enumerate(path_for_each_agent):
        ms = re.findall(path_regex, path)
        path_list = []
        for m in ms:
            m = list(map(lambda x: int(x), m))
            path_list.append((m[1] - 2, m[2] - 2))
        path_lists.append(path_list)
    return path_lists


def _write_output(
    dir_path: Path,
    TA_output: list[list[TaskAssignmentDetails]],
    path_output: list[list[Position]],
    agent_config: AgentConfig,
) -> None:

    # エージェントごとにファイルに書き込む
    for a, ta_list, path_list in zip(agent_config, TA_output, path_output):
        agent_name = a["name"]
        file_path = dir_path / f"{agent_name}.out"
        with open(file_path, "w") as f:
            print(f"{agent_name}", file=f)
            print(f"step:{len(path_list)}", file=f)
            print("task_assignment:", file=f)
            for ta in ta_list:
                if ta.task_name:
                    print(
                        ta.real_step,
                        ta.objective.name,
                        f"name:{ta.task_name}",
                        f"pos:{ta.task_item_pos if ta.objective == Objective.PICK_UP else ta.task_ship_pos}",
                        file=f,
                    )
            print("path:", file=f)
            for p in path_list:
                print(p, file=f)


def _write_output_csv(
    dir_path: Path,
    TA_output: list[list[TaskAssignmentDetails]],
    path_output: list[list[Position]],
    agent_config: AgentConfig,
) -> None:
    csv_path: Path = dir_path / "output.csv"
    header: list[str] = ["steps"]
    for a in agent_config:
        agent_name: str = a["name"]
        header += [
            agent_name + "_path_row",
            agent_name + "_path_col",
            agent_name + "_pick_up",
            agent_name + "_drop_off",
        ]

    steps = max(map(lambda x: len(x), path_output))
    output_array = np.arange(steps)
    for ta_list in TA_output:
        pickups = np.full(steps, "", dtype=object)
        dropoffs = np.full(steps, "", dtype=object)
        for ta in ta_list:
            if ta.objective == Objective.PICK_UP:
                pickups[ta.real_step] += ta.task_name + " "
            elif ta.objective == Objective.DROP_OFF:
                dropoffs[ta.real_step] += ta.task_name + " "
        output_array = np.vstack((output_array, pickups, dropoffs))
    if steps > 0:
        for i, path_list in enumerate(path_output):
            if path_list:
                path_row = np.array(path_list)[:, 0]
                path_col = np.array(path_list)[:, 1]
            else:
                # エージェントが動かなかった場合初期状態を出力
                path_row = [TA_output[i][0].end_point_pos[0]]
                path_col = [TA_output[i][0].end_point_pos[1]]
            path_row = np.concatenate(
                [path_row, np.full(steps - len(path_row), path_row[-1])]
            )
            path_col = np.concatenate(
                [path_col, np.full(steps - len(path_col), path_col[-1])]
            )
            output_array = np.insert(output_array, 1 + 4 * i, path_col, axis=0)
            output_array = np.insert(output_array, 1 + 4 * i, path_row, axis=0)
    np.savetxt(
        csv_path,
        output_array.T,
        delimiter=",",
        fmt="%s",
        header=",".join(header),
        comments="",
    )


def postprocess(
    task_file_path: Path,
    agent_file_path: Path,
    mca_file_path: Path,
    output_dir_path: Path,
) -> list[list[Position]]:
    tasks = _read_task(task_file_path)
    agent_config = read_agent_config(agent_file_path)
    task_assignment, path_for_each_agent = _read_mca_output(mca_file_path)

    TA_output = _format_TA_output(task_assignment, tasks)
    path_output = _format_path_output(path_for_each_agent)

    agent_positions = np.array(
        [tuple(a["pos"]) for a in agent_config], dtype=[("x", int), ("y", int)]
    )
    agent_pos_ids = np.argsort(agent_positions, order=["x", "y"])
    TA_output = [TA_output[i] for i in agent_pos_ids]
    path_output = [path_output[i] for i in agent_pos_ids]
    # 出力をファイルに書き込む
    _write_output(output_dir_path, TA_output, path_output, agent_config)
    _write_output_csv(output_dir_path, TA_output, path_output, agent_config)
    return path_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="postprocess.py")
    parser.add_argument("-t", "--task-path", required=True, type=Path)
    parser.add_argument("-a", "--agent-configs-path", required=True, type=Path)
    parser.add_argument("-MP", "--mca-output-path", required=True, type=Path)
    parser.add_argument("-o", "--output-dir", required=True, type=Path)
    args = parser.parse_args()
    task_file_path: Path = args.task_path
    agent_configs_path: Path = args.agent_configs_path
    mca_file_path: Path = args.mca_output_path
    output_dir_path: Path = args.output_dir
    output_dir_path.mkdir(exist_ok=True, parents=True)
    path_output = postprocess(
        task_file_path, agent_configs_path, mca_file_path, output_dir_path
    )
    print(max(map(lambda x: len(x), path_output)))
