from pydantic import BaseModel

class ComicModel(BaseModel):
    name: str
    url: str