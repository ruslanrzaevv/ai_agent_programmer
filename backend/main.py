from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.incidents import router as incident_router
from routes.websocket import router as websocket_router


app = FastAPI()

app.include_router(incident_router)
app.include_router(websocket_router)


app.add_middleware(
    CORSMiddleware,     
    allow_origins=["*"],  
    allow_methods=["*"],  
    allow_headers=["*"],  
)