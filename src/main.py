from fastapi import FastAPI, Request, HTTPException,  Depends
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict

from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.security import HTTPBasic, HTTPBasicCredentials


import traceback
from pathlib import Path
import sys
import json
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))


USER_NAME = "ai_shop_assistant"
PASSWORD = "ai_shop_assistant"

security = HTTPBasic()


app = FastAPI()

front_dir = current_dir / "front" / "dist"
app.mount("/front", StaticFiles(directory=front_dir), name="front")

js_dir = front_dir / "js"
print(js_dir)
app.mount("/js", StaticFiles(directory=js_dir), name="js")

css_dir = front_dir / "css"
app.mount("/css", StaticFiles(directory=css_dir), name="css")

@app.get("/main")
async def get():
    return FileResponse(front_dir / "index.html")


@app.get("/")
async def index():
    return FileResponse(front_dir / "index.html")

#@app.get("/", response_class=HTMLResponse)
#async def index(credentials: HTTPBasicCredentials = Depends(security)):
#    username = credentials.username
#    password = credentials.password
#
#
#    if username == USER_NAME and password == PASSWORD:
#        return FileResponse(front_dir / "dummy.html")
#    else:
#        error = "ユーザ名かパスワードが間違っています"
#        raise HTTPException(
#            status_code=HTTP_401_UNAUTHORIZED,
#            detail=error,
#            headers={"WWW-Authenticate": "Basic"},
#        )


# Sample data for demonstration purposes
agents = ["agent1", "agent2", "agent3"]
map_configs = ["config123", "config456", "config789"]
stocks = ["stock123", "stock456", "stock789"]
picking_lists = ["list123", "list456", "list789"]

@app.get("/api/agents")
async def get_agents():
    return JSONResponse(content=agents)

@app.get("/api/map-configs")
async def get_map_configs():
    return JSONResponse(content=map_configs)

@app.get("/api/stocks")
async def get_stocks():
    return JSONResponse(content=stocks)

@app.get("/api/picking-lists")
async def get_picking_lists():
    return JSONResponse(content=picking_lists)

@app.post("/api/start")
async def start_process(data: Dict):
    # Extract the data from the request
    agent_ids = data.get('agent_ids')
    map_config_id = data.get('map_config_id')
    stock_id = data.get('stock_id')
    picking_list_id = data.get('picking_list_id')

    # Perform some validation (optional)
    if not agent_ids or not map_config_id or not stock_id or not picking_list_id:
        raise HTTPException(status_code=400, detail="All fields are required")

    # Implement your process logic here
    # This is just a placeholder response
    response_data = {
        "status": "success",
        "message": "Process started successfully",
        "received_data": data
    }

    return JSONResponse(content=response_data)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
