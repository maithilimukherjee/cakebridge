from pydantic import BaseModel
from typing import Optional, Dict

class CakeRequest(BaseModel):
    user_id: int
    description: Optional[str] = None
    image_url: str
    input_type: str

    budget_min: Optional[int]
    budget_max: Optional[int]

    event_date: str
    delivery_city: str

    ai_tags: Optional[Dict] = None