from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional
from pathlib import Path
import shutil
import logging
import base64

from mfutils import generate_random_string, parse_log, parse_route, get_jst_now

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
storage_dir = current_dir / "storage"
agents_dir = storage_dir / "agents"
map_dir = storage_dir / "map_configs"
picking_list_dir = storage_dir / "picking_lists"

USER_NAME = "ai_shop_assistant"
PASSWORD = "ai_shop_assistant"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

front_dir = current_dir / "front" / "dist"
app.mount("/front", StaticFiles(directory=front_dir), name="front")
app.mount("/js", StaticFiles(directory=front_dir / "js"), name="js")
app.mount("/css", StaticFiles(directory=front_dir / "css"), name="css")

@app.get("/main")
async def get():
    return FileResponse(front_dir / "index.html")

@app.get("/")
async def index():
    return FileResponse(front_dir / "index.html")

agents = ["0001", "0002", "0003"]
map_configs = ["0001", "0002", "0003"]
stocks = [
    {"id": "stock001", "created_at": "2024年10月7日10:12:23", "description": "ああああ"},
    {"id": "stock002", "created_at": "2024年10月7日11:12:23", "description": "いいいい"},
    {"id": "stock003", "created_at": "2024年10月7日12:12:23", "description": "うううう"},
    # さらに多くの在庫データが続く...
]
picking_lists = ["0001", "0002", "0003"]

@app.get("/api/agents")
async def get_agents():
    return JSONResponse(content=agents)

@app.get("/api/map-configs")
async def get_map_configs():
    return JSONResponse(content=map_configs)

@app.get("/api/stocks")
async def get_stocks(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    total_stocks = len(stocks)
    paginated_stocks = stocks[offset:offset+limit]
    response_data = {
        "total": total_stocks,
        "stocks": paginated_stocks
    }
    return JSONResponse(content=response_data)

@app.get("/api/picking-lists")
async def get_picking_lists():
    return JSONResponse(content=picking_lists)

async def run_subprocess(command):
    process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return stdout.decode(), stderr.decode()

@app.post("/api/start")
async def start_process(data: Dict):
    agent_ids = data.get('agent_ids')
    map_config_id = data.get('map_config_id')
    stock_id = data.get('stock_id')
    picking_list_id = data.get('picking_list_id')

    if not agent_ids or not map_config_id or not stock_id or not picking_list_id:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    result_id = generate_random_string()
    result_dir = storage_dir / "results" / result_id
    logger.info(f"result_dir: {result_dir}")
    
    command = [
        "python3", 
        current_dir / "behavior_opt/mca/mca.py", 
        "-a", agents_dir / f"{agent_ids[0]}.csv", 
        "-m", map_dir / f"{map_config_id}.json", 
        "-p", picking_list_dir / f"{picking_list_id}.csv", 
        "-o", result_dir
    ]

    try:
        stdout, stderr = await run_subprocess(command)
        print("Output:\n", stdout)

        download_dir = result_dir / "download"
        download_dir.mkdir()
        for p in result_dir.glob("*.out"):
            df = parse_route(p)
            df['順番'] = range(1, len(df) + 1)
            df = df[["順番", "item_id", "pos"]]
            df.to_csv(download_dir / p.with_suffix(".csv").name, index=False, encoding='cp932')

        shutil.make_archive(result_dir / "download", 'zip', download_dir)

        response_data = parse_log(stdout)    
        response_data["result_id"] = result_id
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        response_data = {"message": str(e)}
        return JSONResponse(status_code=500, content=response_data)

@app.get("/api/download/{result_id}")
async def download_results(result_id: str):
    logger.info(f"result_dir: {result_id}")

    file_path = storage_dir / "results" / result_id / "download.zip"
    logger.info(f"file_path: {file_path}")

    if file_path.exists():
        now = get_jst_now()
        return FileResponse(path=str(file_path), filename=f"download_{now}.zip", media_type="application/zip")
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/visualize")
async def start_visualize(data: Dict):
    agent_ids = data.get('agent_ids')
    map_config_id = data.get('map_config_id')
    stock_id = data.get('stock_id')
    picking_list_id = data.get('picking_list_id')
    result_id = data.get('result_id')

    if not agent_ids or not map_config_id or not stock_id or not picking_list_id or not result_id:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    result_dir = storage_dir / "results" / result_id
    logger.info(f"result_dir: {result_dir}")

    output_gif_path = result_dir / "output.gif"

    command = [
        "python3", 
        current_dir / "behavior_opt/visualizer.py", 
        "-a", agents_dir / f"{agent_ids[0]}.csv", 
        "-m", map_dir / f"{map_config_id}.json", 
        "-p", picking_list_dir / f"{picking_list_id}.csv", 
        "-B", result_dir / "output.csv",
        "-o", output_gif_path
    ]

    try:
        stdout, stderr = await run_subprocess(command)
        print("Output:\n", stdout)

        with open(output_gif_path, "rb") as gif_file:
            gif_data = gif_file.read()

        encoded_gif = base64.b64encode(gif_data).decode('utf-8')
        response_data = {"gif": encoded_gif}
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        response_data = {"message": str(e)}
        return JSONResponse(status_code=500, content=response_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)