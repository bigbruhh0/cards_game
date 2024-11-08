from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True, index=True)
	hashed_password = Column(String)
	coins = Column(Integer, default=0)
	gems = Column(Integer, default=0)
	cards = relationship("UserCard", back_populates="user")
	boxes = relationship("UserBox", back_populates="user")

class Box(Base):
    __tablename__ = "boxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    coins_price=Column(Integer,default=0)
    gems_price=Column(Integer,default=0)

class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    rarity = Column(String)

# Модель карты
class UserCard(Base):
    __tablename__ = "user_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))

    user = relationship("User", back_populates="cards")
    card = relationship("Card")


class UserBox(Base):
    __tablename__ = "user_boxes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    box_id = Column(Integer, ForeignKey("boxes.id"))

    user = relationship("User", back_populates="boxes")
    box = relationship("Box")

class BoxContent(Base):
    __tablename__ = "box_contents"

    id = Column(Integer, primary_key=True, index=True)
    box_id = Column(Integer, ForeignKey("boxes.id"))
    card_id = Column(Integer, ForeignKey("cards.id"))

    box = relationship("Box")
    card = relationship("Card")
class BuyOrderModel(Base): 
	__tablename__= "payment_body"
	id = Column(Integer, primary_key=True, index=True)
	cost = Column(Integer)
	coins = Column(Integer,default=0)
	gems = Column(Integer,default=0)

class BuyOrderPending(Base):
	__tablename__= "payment_pending"
	id = Column(Integer, primary_key=True, index=True)
	buy_id = Column(Integer)
	user_id = Column(Integer)
	type = Column(Integer)
	uuid = Column(String)
	
class BuyOrderCompleted(Base):
	__tablename__= "payment_completed"
	id = Column(Integer, primary_key=True, index=True)
	buy_id = Column(Integer)
	user_id = Column(Integer)
	type = Column(Integer)
	uuid = Column(String)
class PaymentServices(Base):
	__tablename__="payment_services"
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
