from pydantic import BaseModel


class DropdownItem(BaseModel):
    id: int
    name: str
