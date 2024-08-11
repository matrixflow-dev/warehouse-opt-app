from fastapi import FastAPI, HTTPException,  Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles
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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
