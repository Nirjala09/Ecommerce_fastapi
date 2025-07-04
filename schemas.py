from pydantic import BaseModel, EmailStr
from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    name: str
    description: str | None = None
    price: float

class UserCreate(BaseModel):
    email: str
    password: str
    role: Optional[str] = "user" 

class UserOut(BaseModel):
    id: int
    email: str
    role: str 
    
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int