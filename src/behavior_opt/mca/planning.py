import argparse
import subprocess
import time
from pathlib import Path

from behavior_opt.utils.file_io import read_agent_config


def behavior_opt(
    agent_config_path: Path,
    output_dir: Path,
    any_time: bool = False,
    time_limit: int = 30,
) -> None:
    """MCA-RMCAを実行する"""
    agents = read_agent_config(agent_config_path)
    capacity: list[int] = [int(agent["capacity"]) for agent in agents]
    cmd = ["./MCA-RMCA/build/MAPD"]
    # map
    cmd.append("-m")
    cmd.append(str(output_dir / "storehouse.map"))
    # agent
    cmd.append("-a")
    cmd.append(str(output_dir / "storehouse.map"))
    # task
    cmd.append("-t")
    cmd.append(str(output_dir / "storehouse.task"))
    # capacity
    cmd.append("--capacity")
    for c in capacity:
        cmd.append(str(c))
    # solver:  "ICBS", "CBS", "CBSH", "CBSH-CR", "CBSH-R", "CBSH-RM", "CBSH-GR", "PBS", "PP", "REGRET"
    cmd.append("-s")
    cmd.append("PP")
    # time limit
    cmd.append("-c")
    cmd.append(str(time_limit))
    # screen
    cmd.append("--screen")
    cmd.append("1")
    # other options
    cmd.append("--only-update-top")
    cmd.append("--kiva")
    cmd.append("--objective")
    cmd.append(
        "makespan"
    )  # 早くするにはtotal-travel-delay, stepを小さくするにはmakespan

    # cmd.append("--multi-label")
    if any_time:
        cmd.append("--anytime")
    subprocess.run(cmd, stdout=open(output_dir / "storehouse.out", "w"), check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="planning.py")
    parser.add_argument("-a", "--agent-config-path", required=True, type=Path)
    parser.add_argument("-MD", "--mca-output-dir", required=True, type=Path)
    args = parser.parse_args()
    agent_config_path: Path = args.agent_config_path
    output_dir: Path = args.mca_output_dir
    # MCA-RMCAを実行
    start_time = time.time()
    behavior_opt(agent_config_path, output_dir)
    elapsed_time = time.time() - start_time
    print(f"elapsed_time:{elapsed_time}")
