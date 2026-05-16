from pydantic import BaseModel

class IncidentRequest(BaseModel):
    logs: str

class ApproveFixRequest(BaseModel):
    file_path: str
    new_code: str
    commit_message: str