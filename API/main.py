from fastapi import FastAPI, Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import models, schemas, auth 
from database import engine, get_db
import random

from yoomoney import Client

from yoomoney import Quickpay
from uuid import uuid4


_host="http://127.0.0.1:8000/"

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
	print(token)
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
    
	try:
		payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
		print(payload)
		username: str = payload.get("sub")
		if username is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	user = db.query(models.User).filter(models.User.username == username).first()
	if user is None:
		raise credentials_exception

	return user

@app.post("/register/", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password,coins=6,gems=5)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    starter_boxes = db.query(models.Box).filter(models.Box.name.in_(["Starter box"])).all()
    for box in starter_boxes:
        user_box = models.UserBox(user_id=new_user.id, box_id=box.id)
        db.add(user_box)
    db.commit()
    return new_user

@app.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):  
    return current_user

@app.get("/usesr/me")
def read_users_me(request:Request): 
	headers = request.headers

	for key, value in headers.items():
		print(f"{key}: {value}")

	return {"Authorization": 123, "message": "Headers received"}


@app.post("/user/open_box/",response_model=schemas.OpenBoxResponse)
async def open_box(box_open: schemas.BoxOpen, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
	user_box = db.query(models.UserBox).filter(models.UserBox.user_id == current_user.id, models.UserBox.box_id == box_open.box_id).first()
	if not user_box:
		raise HTTPException(status_code=404, detail="Box not found for this user.")

	box_contents = db.query(models.BoxContent).filter(models.BoxContent.box_id == box_open.box_id).all()
	if not box_contents:
		raise HTTPException(status_code=404, detail="Box is empty.")
	cards=[]
	for i in range(3):

		selected_card = random.choice(box_contents).card

		user_card = models.UserCard(user_id=current_user.id, card_id=selected_card.id)
		db.add(user_card)
		card = db.query(models.Card).filter(models.Card.id == selected_card.id).first()
		cards.append(schemas.GetOpenedCards(card_id=selected_card.id,card_name=card.name,card_rarity=card.rarity))

	db.delete(user_box)
	db.commit()

	return {"got_cards":cards}

@app.post("/user/get_cards/", response_model=list[schemas.UserCardsResponse])
async def get_user_cards( current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
	print(current_user.id)
	user_cards = db.query(models.UserCard).filter(models.UserCard.user_id == current_user.id).all()
	cards=[]
	if not user_cards:
		return cards

	for user_card in user_cards:
		card = db.query(models.Card).filter(models.Card.id == user_card.card_id).first()
		if card:
			cards.append(schemas.UserCardsResponse(card_id=card.id, card_name=card.name, card_rarity=card.rarity))

	return cards
	
@app.post("/user/get_boxes/", response_model=list[schemas.UserBoxesResponse])
async def get_user_boxes( current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_boxes = db.query(models.UserBox).filter(models.UserBox.user_id == current_user.id).all()
    boxes = []
    if not user_boxes:
        return boxes

    
    for user_box in user_boxes:
        box = db.query(models.Box).filter(models.Box.id == user_box.box_id).first()
        if box:
            boxes.append(schemas.UserBoxesResponse(box_id=box.id, box_name=box.name))
    
    return boxes

@app.post("/user/buy_box/")
def buy_box(request_box:schemas.BuyBox, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    box_id=request_box.box_id
    box = db.query(models.Box).filter(models.Box.id == box_id).first()
    print(box.id,box.coins_price,box.gems_price)
    
    if not box:
        raise HTTPException(status_code=404, detail="Box not found")

    if current_user.coins < box.coins_price and current_user.gems < box.gems_price:  # Предполагается, что у бокса есть поле price
        raise HTTPException(status_code=400, detail="Not enough currency to buy the box")

    current_user.coins -= box.coins_price
    current_user.gems  -= box.gems_price
    db.commit()
    new_box = models.UserBox(user_id=current_user.id, box_id=box_id)
    db.add(new_box)
    db.commit()

    return {"message": "Box purchased successfully", "box_id": new_box.id}
@app.post("/user/buy/")
def process_buying(buy_scheme:schemas.BuyOrder,current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
	print("Пришел запрос на покупку валюты",buy_scheme.buy_id)
	_type=1
	buy_id=buy_scheme.buy_id
	buy_order = db.query(models.BuyOrderModel).filter(models.BuyOrderModel.id == buy_id).first()
	if buy_order:
		print(f"ID: {buy_order.id}, Cost: {buy_order.cost}, Coins: {buy_order.coins}, Gems: {buy_order.gems}")
		cost=buy_order.cost
		coins=buy_order.coins
		gems=buy_order.gems
		_uuid=str(uuid4())
		redirect_url=_host+f"checkPayment/{_uuid}"
		
		quickpay = Quickpay(
			receiver="4100116711308983",
			quickpay_form="shop",
			targets="Тестовая покупка",
			paymentType="SB",
			sum=2,
			label=_uuid,
			successURL=redirect_url
		)
		if quickpay:
			new_order = models.BuyOrderPending(buy_id=buy_id, user_id=current_user.id, type=_type,uuid=_uuid)
			db.add(new_order)
			db.commit()
			db.refresh(new_order)
			print(quickpay.base_url)
			print(quickpay.redirected_url)
			return {"payment_url":quickpay.redirected_url}
		else:
			print("Error while creating payment form")
	else:
		print("No record found with that ID.")
	return {"message": "Succesfull request", "buy_id": buy_scheme.buy_id}
@app.post("/yoomoney/webhook/")
async def yoomoney_webhooks(request:Request, db: Session = Depends(get_db)):
	form_data=await request.form()
	print("got payment ")
	print(form_data)
	label = form_data.get("label")
	print(f'label:{label}')
	buy_order = db.query(models.BuyOrderPending).filter(models.BuyOrderPending.uuid == label).first()
	
	if buy_order:
		completed_order=models.BuyOrderCompleted(buy_id=buy_order.buy_id, user_id=buy_order.user_id, type=buy_order.type,uuid=buy_order.uuid)
		db.add(completed_order)
		db.delete(buy_order)
		buy_body=db.query(models.BuyOrderModel).filter(models.BuyOrderModel.id==buy_order.buy_id).first()
		_user=db.query(models.User).filter(models.User.id==buy_order.user_id).first()
		_user.coins+=buy_body.coins
		_user.gems+=buy_body.gems
		db.commit()
		print('SUCCESS')
	return {"status": "ok"}
@app.get("/checkPayment/{uuid}")
async def check_payment(uuid: str):
    return {"message": "Payment successful", "uuid": uuid}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
