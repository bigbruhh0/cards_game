from pydantic import BaseModel
from typing import List
class UserCreate(BaseModel):
    username: str
    password: str

class LoginData(BaseModel):
    username: str
    password: str

class User(BaseModel):
	id: int
	username: str
	coins: int
	gems: int
	class Config:
		from_attributes = True
class BoxOpen(BaseModel):
	box_id:int

class UserBoxesResponse(BaseModel):
    box_id: int
    box_name: str

class UserCardsResponse(BaseModel):
    card_id: int
    card_name: str
    card_rarity: str
class BuyBox(BaseModel):
	box_id: int
class BuyOrder(BaseModel):
	buy_id: int
class GetOpenedCards(BaseModel):
	card_id:int
	card_name:str
	card_rarity:str

class OpenBoxResponse(BaseModel):
    got_cards: List[GetOpenedCards]
