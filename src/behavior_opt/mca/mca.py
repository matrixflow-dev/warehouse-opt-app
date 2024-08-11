import argparse
from pathlib import Path
import time

from behavior_opt.mca.preprocess import preprocess
from behavior_opt.mca.planning import behavior_opt
from behavior_opt.mca.postprocess import postprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="mca.py")
    parser.add_argument("-a", "--agent-config-path", required=True, type=Path)
    parser.add_argument("-i", "--item-config-path", required=False, type=Path)
    parser.add_argument("-m", "--map-config-path", required=True, type=Path)
    parser.add_argument("-c", "--config-path", required=False, type=Path)
    parser.add_argument("-p", "--picking-list-path", required=True, type=Path)
    parser.add_argument("-o", "--output-dir", required=True, type=Path)
    args = parser.parse_args()
    map_config_path: Path = args.map_config_path
    config_path = args.config_path
    agent_config_path: Path = args.agent_config_path
    item_config_path = args.item_config_path
    picking_list_path: Path = args.picking_list_path
    output_dir_path: Path = args.output_dir
    mca_output_dir: Path = output_dir_path / "mca"

    output_dir_path.mkdir(exist_ok=True, parents=True)
    mca_output_dir.mkdir(exist_ok=True)

    start_time = time.time()
    print("preprocessing...")
    preprocess(
        map_config_path=map_config_path,
        agent_config_path=agent_config_path,
        item_config_path=item_config_path,
        picking_list_path=picking_list_path,
        output_dir=mca_output_dir,
        config_path=config_path,
    )
    print("planning...")
    behavior_opt(agent_config_path, mca_output_dir)
    task_file_path = mca_output_dir / "tasks.csv"
    mca_file_path = mca_output_dir / "storehouse.out"
    print("postprocessing...")
    path_output = postprocess(
        task_file_path, agent_config_path, mca_file_path, output_dir_path
    )
    elapsed_time = time.time() - start_time
    print(f"elapsed_time:{elapsed_time}")
    print(f"makespan:{max(map(lambda x: len(x), path_output))}")
    print(f"avg steps:{sum(map(lambda x: len(x), path_output))/len(path_output)}")
    for i, path in enumerate(path_output):
        print(f"agent:{i} steps:{len(path)}")
