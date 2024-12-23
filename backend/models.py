from pydantic import BaseModel


class Update(BaseModel):
    description: str
    hours: int

    def __hash__(self):
        return hash(self.description)


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
