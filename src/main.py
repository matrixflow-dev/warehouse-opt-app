from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional
from pathlib import Path
import shutil
import logging
import base64
import asyncio
import subprocess
import json
import pandas as pd
from fastapi import FastAPI, WebSocket, HTTPException,  Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from mfutils import parse_log, parse_route, get_jst_now
from stock_management import generate_rack_layout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_NAME = "warehouse_ai_mf"
PASSWORD = "warehouse_ai_mf"

security = HTTPBasic()

current_dir = Path(__file__).resolve().parent
storage_dir = current_dir / "storage"
agents_dir = storage_dir / "agents" / "group"
map_dir = storage_dir / "map_configs"
stocks_dir = storage_dir / "stocks"
picking_list_dir = storage_dir / "picking_lists"
results_dir = storage_dir / "results"

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


@app.get("/", response_class=HTMLResponse)
async def index(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password


    if username == USER_NAME and password == PASSWORD:
        return FileResponse(front_dir / "index.html")
    else:
        error = "ユーザ名かパスワードが間違っています"
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Basic"},
        )



def load_meta_data(dir_path: Path, resource_name: str):
    """
    Load the meta.json file from the given directory.

    Args:
        dir_path (Path): The directory where the meta.json file is located.
        resource_name (str): The name of the resource for error messages.

    Returns:
        dict: The content of the meta.json file.

    Raises:
        HTTPException: If the directory or meta.json file does not exist.
    """
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail=f"{resource_name} not found")
    
    meta_path = dir_path / "meta.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Meta information not found")
    
    with open(meta_path, "r") as f:
        return json.load(f)

def get_next_number(directory: Path) -> str:
    """
    Get the next available number for a new directory in the specified path.

    Args:
        directory (Path): The directory where the new numbered directory will be created.

    Returns:
        str: The next available number, zero-padded to 4 digits.
    """
    sorted_dirs = sorted(directory.iterdir(), key=lambda x: int(x.name), reverse=True)
    if len(sorted_dirs) > 0:
        highest_number = int(sorted_dirs[0].name)
        next_number = highest_number + 1
    else:
        next_number = 1
    return str(next_number).zfill(4)

############### stocks start ##########################
@app.get("/api/stocks")
async def get_stocks(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    sorted_dirs = sorted(stocks_dir.iterdir(), key=lambda x: int(x.name), reverse=True)
    sorted_meta_paths = [dir_path / "meta.json" for dir_path in sorted_dirs if dir_path.is_dir()]

    total_stocks = len(sorted_meta_paths)
    paginated_stocks_paths = sorted_meta_paths[offset:offset+limit]

    paginated_stocks = []
    for p in paginated_stocks_paths:
        try:
            with open(p) as f:
                d = json.load(f)
                paginated_stocks.append(d)
        except Exception as e:
            logger.info(f"{e}")
            logger.info(f"cannot get path: {p}")
    response_data = {
        "total": total_stocks,
        "stocks": paginated_stocks
    }
    return JSONResponse(content=response_data)

@app.post("/api/stocks")
async def add_stock(
    name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        next_number = get_next_number(stocks_dir)

        target_dir = stocks_dir / next_number
        target_dir.mkdir()
        try:
            json_data = json.load(file.file)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
           
        file_path = target_dir / "info.json"
        with open(file_path, "w") as f:
            json.dump(json_data, f, indent=4)
        
        meta_info = {
            "id": next_number,
            "name": name,
            "description": description,
            "created_at": get_jst_now(format="record")
        }
        meta_path = target_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta_info, f, indent=4)
        
        return JSONResponse(content={"message": "File uploaded successfully", "id": next_number})

    except Exception as e:
        logger.error("Error occurred while uploading the file: %s", str(e))
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/api/stocks/{id}")
async def get_stock(id: str):
    try:
        target_dir = stocks_dir / id
        stock_info = load_meta_data(target_dir, "Stock Information")
        return JSONResponse(content={"stock": stock_info})
    
    except Exception as e:
        logger.error("Error occurred while retrieving the Stock Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Stock Information")

@app.delete("/api/stocks/{id}")
async def delete_stock(id: str):
    try:
        target_dir = stocks_dir / id
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="Stock Information not found")
        
        shutil.rmtree(target_dir)
        return JSONResponse(content={"message": f"Stock Information {id} has been deleted successfully."})
    
    except Exception as e:
        logger.error("Error occurred while deleting the Stock Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete Stock Information")

############### stocks end ##########################

############### picking-lists start ##########################

@app.get("/api/picking-lists")
async def get_picking_lists(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    
    sorted_dirs = sorted(picking_list_dir.iterdir(), key=lambda x: int(x.name), reverse=True)
    sorted_meta_paths = [dir_path / "meta.json" for dir_path in sorted_dirs if dir_path.is_dir()]

    total_lists = len(sorted_meta_paths)
    paginated_list_paths = sorted_meta_paths[offset:offset+limit]

    paginated_stocks = []
    for p in paginated_list_paths:
        try:
            with open(p) as f:
                d = json.load(f)
                paginated_stocks.append(d)
        except Exception as e:
            logger.info(f"{e}")
            logger.info(f"cannot get path: {p}")

    response_data = {
        "total": total_lists,
        "pickingLists": paginated_stocks
    }
    return JSONResponse(content=response_data)


@app.post("/api/picking-lists")
async def add_picking_list(
    name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        next_number = get_next_number(picking_list_dir)

        target_dir = picking_list_dir / next_number
        target_dir.mkdir()
        target_path = target_dir / "list.csv"
        with open(target_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        meta_info = {
            "id": next_number,
            "name": name,
            "description": description,
            "created_at": get_jst_now(format="record")
        }
        meta_path = target_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta_info, f, indent=4)
        
        return JSONResponse(content={"message": "Picking list uploaded successfully", "id": next_number})

    except Exception as e:
        logger.error("Error occurred while uploading the file: %s", str(e))
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/api/picking-lists/{id}")
async def get_picking_list(id: str):
    try:
        target_dir = picking_list_dir / id
        picking_list_info = load_meta_data(target_dir, "picking-lists")
        return JSONResponse(content={"pickingList": picking_list_info})
    
    except Exception as e:
        logger.error("Error occurred while retrieving the picking-lists: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve picking-lists")

@app.delete("/api/picking-lists/{id}")
async def delete_picking_list(id: str):
    try:
        target_dir = picking_list_dir / id
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="picking-lists not found")
        
        shutil.rmtree(target_dir)
        return JSONResponse(content={"message": f"picking-lists {id} has been deleted successfully."})
    
    except Exception as e:
        logger.error("Error occurred while deleting the picking-lists: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete picking-lists")

############### picking-lists end ##########################

############### agents start ##########################

@app.get("/api/agents")
async def get_agents(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    sorted_dirs = sorted(agents_dir.iterdir(), key=lambda x: int(x.name), reverse=True)
    sorted_meta_paths = [dir_path / "meta.json" for dir_path in sorted_dirs if dir_path.is_dir()]

    total_agents = len(sorted_meta_paths)
    paginated_agent_paths = sorted_meta_paths[offset:offset+limit]

    paginated_agents = []
    for p in paginated_agent_paths:
        try:
            with open(p) as f:
                d = json.load(f)
                paginated_agents.append(d)
        except Exception as e:
            logger.info(f"cannot get path: {p}")
    
    response_data = {
        "total": total_agents,
        "agents": paginated_agents
    }
    return JSONResponse(content=response_data)

@app.post("/api/agents")
async def add_agent(
    agent_data: Dict = Body(...)
):
    try:
        next_number = get_next_number(agents_dir)

        target_dir = agents_dir / next_number
        target_dir.mkdir()

        meta_info = {
            "id": next_number,
            "name": agent_data['name'],
            "description": agent_data['description'],
            "created_at": get_jst_now(format="record")
        }
        meta_path = target_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta_info, f, indent=4)
        
        group = agent_data['group']
        df = pd.DataFrame(group)
        df = df[["agent_id","amount","initial_place_row","initial_place_col","name"]]
        df.to_csv(target_dir / "agents_info.csv", index=False)
        
        return JSONResponse(content={"message": "Agent added successfully", "id": next_number})

    except Exception as e:
        print(f"Error occurred while adding the agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add agent")

@app.get("/api/agents/{id}")
async def get_agent(id: str):
    try:
        target_dir = agents_dir / id
        agent_info = load_meta_data(target_dir, "Agent Information")
        
        df = pd.read_csv(target_dir / "agents_info.csv")
        group = df.to_dict(orient="records")
        agent_info["group"] = group

        return JSONResponse(content={"agent": agent_info})
    
    except Exception as e:
        logger.error("Error occurred while retrieving the Agent Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Agent Information")

@app.delete("/api/agents/{id}")
async def delete_agent(id: str):
    try:
        target_dir = agents_dir / id
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="Agent Information not found")
        
        shutil.rmtree(target_dir)
        return JSONResponse(content={"message": f"Agent Information {id} has been deleted successfully."})
    
    except Exception as e:
        logger.error("Error occurred while deleting the Agent Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete Agent Information")

############### agents end ##########################

############### map-configs start ##########################

@app.get("/api/map-configs")
async def get_map_configs(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):

    sorted_dirs = sorted(map_dir.iterdir(), key=lambda x: int(x.name), reverse=True)
    sorted_meta_paths = [dir_path / "meta.json" for dir_path in sorted_dirs if dir_path.is_dir()]

    total_map_configs = len(sorted_meta_paths)
    paginated_map_paths = sorted_meta_paths[offset:offset+limit]

    paginated_map_configs = []
    for p in paginated_map_paths:
        try:
            with open(p) as f:
                d = json.load(f)
                paginated_map_configs.append(d)
        except Exception as e:
            logger.info(f"cannot get path: {p}")
    
    response_data = {
        "total": total_map_configs,
        "mapConfigs": paginated_map_configs
    }
    return JSONResponse(content=response_data)


@app.post("/api/map-configs")
async def upload_map_config(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...)
):
    try:
        next_number = get_next_number(map_dir)

        target_dir = map_dir / next_number
        target_dir.mkdir()
        try:
            json_data = json.load(file.file)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        
        generate_rack_layout(json_data, target_dir)
        
        file_path = target_dir / "config.json"
        with open(file_path, "w") as f:
            json.dump(json_data, f, indent=4)
        
        meta_info = {
            "id": next_number,
            "name": name,
            "description": description,
            "created_at": get_jst_now(format="record")
        }
        meta_path = target_dir / "meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta_info, f, indent=4)
        
        return JSONResponse(content={"message": "File uploaded successfully", "id": next_number})

    except Exception as e:
        logger.error("Error occurred while uploading the file: %s", str(e))
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/api/map-configs/{id}")
async def get_map_config(id: str):
    try:
        target_dir = map_dir / id
        map_config = load_meta_data(target_dir, "Map configuration")
        return JSONResponse(content={"mapConfig": map_config})
    
    except Exception as e:
        logger.error("Error occurred while retrieving the map configuration: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve map configuration")

@app.get("/api/map-configs/{id}/rack-layout")
async def get_rack_layout(id: str):
    try:
        target_dir = map_dir / id
        rack_layout_path = target_dir / "rack_layout.html"
        if not rack_layout_path.exists():
            raise HTTPException(status_code=404, detail="rack_layout.html not found")
        return FileResponse(path=str(rack_layout_path), media_type="text/html")
    except Exception as e:
        logger.error(f"Failed to retrieve rack_layout.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rack_layout.html")
    
@app.delete("/api/map-configs/{id}")
async def delete_map_config(id: str):
    try:
        target_dir = map_dir / id
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="Map configuration not found")
        
        shutil.rmtree(target_dir)
        return JSONResponse(content={"message": f"Map configuration {id} has been deleted successfully."})
    
    except Exception as e:
        logger.error("Error occurred while deleting the map configuration: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete map configuration")

############### map-configs end ##########################

@app.get("/api/api")
async def get_api():

    response_data = {
        "endpoint": "https://warehouse-opt-ai.dev1.matrixflow.net/api/v1/",
        "secret_key": "8c00d286-f0eb-9b17-ba17-63931c44c884"
    }
    return JSONResponse(content=response_data)


@app.get("/api/results")
async def get_results(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1)):
    sorted_dirs = sorted(results_dir.iterdir(), key=lambda x: int(x.name), reverse=True)
    sorted_meta_paths = [dir_path / "result.json" for dir_path in sorted_dirs if dir_path.is_dir()]

    total_results = len(sorted_meta_paths)
    paginated_results_paths = sorted_meta_paths[offset:offset+limit]

    paginated_results = []
    for p in paginated_results_paths:
        try:
            with open(p) as f:
                d = json.load(f)
                paginated_results.append(d)
        except Exception as e:
            logger.info(f"{e}")
            logger.info(f"cannot get path: {p}")
    response_data = {
        "total": total_results,
        "results": paginated_results
    }
    return JSONResponse(content=response_data)

@app.get("/api/results/{id}")
async def get_result(id: str):
    try:
        target_dir = results_dir / id
        result_path = target_dir / "result.json"
        if not result_path.exists():
            raise HTTPException(status_code=404, detail="Result Information not found")
        
        with open(result_path, "r") as f:
            result_info = json.load(f)

        output_gif_path = target_dir / "output.gif"
        with open(output_gif_path, "rb") as gif_file:
            gif_data = gif_file.read()

        encoded_gif = base64.b64encode(gif_data).decode('utf-8')
        result_info["gif"] = encoded_gif
        
        return JSONResponse(content={"result": result_info})
    
    except Exception as e:
        logger.error("Error occurred while retrieving the Result Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve Result Information")

@app.delete("/api/results/{id}")
async def delete_result(id: str):
    try:
        target_dir = results_dir / id
        
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="Result Information not found")
        
        shutil.rmtree(target_dir)
        return JSONResponse(content={"message": f"Result Information {id} has been deleted successfully."})
    
    except Exception as e:
        logger.error("Error occurred while deleting the Result Information: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to delete Result Information")

############### results end ##########################


############### home(main) api start ##########################

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
    

    next_number = get_next_number(results_dir)
    
    result_id = next_number
    result_dir = results_dir / result_id
    logger.info(f"result_dir: {result_dir}")
    
    command = [
        "python3", 
        current_dir / "behavior_opt/mca/mca.py", 
        "-a", agents_dir / f"{agent_ids}/agents_info.csv", 
        "-m", map_dir / f"{map_config_id}/config.json", 
        "-s", stocks_dir / f"{stock_id}/info.json", 
        "-p", picking_list_dir / f"{picking_list_id}/list.csv", 
        "-o", result_dir
    ]

    try:
        stdout, stderr = await run_subprocess(command)
        print("Output:\n", stdout)
        print("Output Error:\n", stderr)
        if stderr:
            raise Exception(stderr)

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


        stock_info = load_meta_data(stocks_dir / stock_id, "Stock Information")
        picking_list_info = load_meta_data(picking_list_dir / picking_list_id, "picking-lists")
        agent_info = load_meta_data(agents_dir / agent_ids, "Agent Information")
        map_config = load_meta_data(map_dir / map_config_id, "Map configuration")

        response_data["req_params"] = {
            "agent": agent_info,
            "map_config": map_config,
            "stock": stock_info,
            "picking_list": picking_list_info,
        }
        response_data["created_at"] = get_jst_now(format="record")

        with open(result_dir / "result.json", "w") as f:
            json.dump(response_data, f, indent=4)
    
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error("Error occurred: %s", str(e))
        response_data = {"message": str(e)}
        return JSONResponse(status_code=500, content=response_data)

@app.get("/api/download/{result_id}")
async def download_results(result_id: str):
    logger.info(f"result_dir: {result_id}")

    file_path = results_dir / result_id / "download.zip"
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
    
    result_dir = results_dir / result_id
    logger.info(f"result_dir: {result_dir}")

    output_gif_path = result_dir / "output.gif"

    command = [
        "python3", 
        current_dir / "behavior_opt/visualizer.py", 
        "-a", agents_dir / f"{agent_ids}/agents_info.csv", 
        "-m", map_dir / f"{map_config_id}/config.json", 
        "-s", stocks_dir / f"{stock_id}/info.json", 
        "-p", picking_list_dir / f"{picking_list_id}/list.csv", 
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

############### home(main) api end ##########################

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
