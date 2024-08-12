import secrets
import string
import re
import pandas as pd
from datetime import datetime, timedelta



def get_jst_now(format="file"):
    """
     format file or record
    """
    current_time = datetime.utcnow()
    now_jst = current_time + timedelta(hours=9)
    if format == "file":
        now_jst_string = now_jst.strftime('%Y_%m_%d_%H_%M_%S')
    elif format == "record":
        now_jst_string = now_jst.strftime('%Y年%m月%d日 %H時%M分%S秒')
    return now_jst_string

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for i in range(length))
    return random_string

def parse_log(log_str):
    # 辞書を初期化
    parsed_data = {
        "elapsed_time": None,
        "makespan": None,
        "avg_steps": None,
        "agents": {}
    }

    # 正規表現を使って値を抽出
    elapsed_time_match = re.search(r"elapsed_time:(\d+\.\d+)", log_str)
    makespan_match = re.search(r"makespan:(\d+)", log_str)
    avg_steps_match = re.search(r"avg steps:(\d+\.\d+)", log_str)
    agent_steps_matches = re.findall(r"agent:(\d+) steps:(\d+)", log_str)

    # 抽出した値を辞書に格納
    if elapsed_time_match:
        parsed_data["elapsed_time"] = round(float(elapsed_time_match.group(1)), 3)
    if makespan_match:
        parsed_data["makespan"] = int(makespan_match.group(1))
    if avg_steps_match:
        parsed_data["avg_steps"] = float(avg_steps_match.group(1))
    if agent_steps_matches:
        for agent, steps in agent_steps_matches:
            parsed_data["agents"][int(agent)] = int(steps)

    return parsed_data


def parse_route(filepath):

    with open(filepath) as f:
        data = f.read()
    pick_up_lines = re.findall(r'PICK_UP name:(\d+) pos:\((\d+), (\d+)\)', data)

    # DataFrameに変換
    df = pd.DataFrame(pick_up_lines, columns=['item_id', 'x_pos', 'y_pos'])
    df['item_id'] = df['item_id'].astype('string')
    df['pos'] = df[['x_pos', 'y_pos']].apply(lambda x: f"({x[0]}, {x[1]})", axis=1)
    df = df.drop(columns=['x_pos', 'y_pos'])
    return df