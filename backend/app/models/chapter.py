from pydantic import BaseModel

class ChapterModel(BaseModel):
    name: str
    number: int
    url: str