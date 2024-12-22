from pydantic import BaseModel


class Update(BaseModel):
    description: str
    hours: int

class Ship(BaseModel):
    name: str

    # URLs
    repo: str
    demo: str
    preview: str

    hours: int
    updates: list[Update] = []

class User(BaseModel):
    id: str  # Slack User ID 
    name: str
    ships: list[Ship] = []
