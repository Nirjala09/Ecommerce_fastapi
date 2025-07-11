from fastapi import FastAPI, HTTPException
from database import database, engine, metadata
from models import products, users
from schemas import Product, UserCreate, UserOut, CartItemCreate, CartItemOut
from sqlalchemy import select
from passlib.context import CryptContext
from models import cart
from fastapi import Depends
from auth import get_current_user, require_admin
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="🛍️ E-Commerce API",
    description="A FastAPI backend for e-commerce with JWT authentication, admin-only routes, and cart management.",
    version="1.0.0",
    contact={
        "name": "Nirjala Karki",
        "email": "nirjalakarki09@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)

metadata.create_all(engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()




@app.put("/products/{product_id}", dependencies=[Depends(require_admin)], tags=["Products"])
async def create_product(product: Product):
    query = products.insert().values(
        name=product.name, description=product.description, price=product.price
    )
    last_record_id = await database.execute(query)
    return {**product.dict(), "id": last_record_id}



@app.put("/products/{product_id}", dependencies=[Depends(require_admin)], tags=["Products"])
async def update_product(product_id: int, product: Product):
    query = products.update().where(products.c.id == product_id).values(
        name=product.name,
        description=product.description,
        price=product.price
    )
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product updated successfully"}





@app.post("/users/", response_model=UserOut, tags=["Users"])
async def create_user(user: UserCreate):
    
    query = users.select().where(users.c.email == user.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    
    hashed_password = pwd_context.hash(user.password)

   
    query = users.insert().values(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    user_id = await database.execute(query)
    return {"id": user_id, "email": user.email, "role": user.role}




@app.post("/cart/", response_model=CartItemOut, tags=["Cart"])
async def add_to_cart(item: CartItemCreate, current_user=Depends(get_current_user)):
    product_query = products.select().where(products.c.id == item.product_id)
    product = await database.fetch_one(product_query)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = cart.insert().values(
        product_id=item.product_id,
        quantity=item.quantity,
        user_id=current_user["id"] 
    )
    cart_id = await database.execute(query)
    return {**item.dict(), "id": cart_id}


@app.get("/cart/", response_model=list[CartItemOut], tags=["Cart"])
async def view_cart():
    query = cart.select()
    return await database.fetch_all(query)

@app.delete("/products/{product_id}", dependencies=[Depends(require_admin)], tags=["Products"])
async def delete_product(product_id: int):
    delete_cart_query = cart.delete().where(cart.c.product_id == product_id)
    await database.execute(delete_cart_query)
    product_query = products.delete().where(products.c.id == product_id)
    result = await database.execute(product_query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product and related cart items deleted successfully"}




@app.delete("/cart/{cart_item_id}", tags=["Cart"])
async def delete_cart_item(cart_item_id: int, current_user=Depends(get_current_user)):
   
    query = cart.select().where(cart.c.id == cart_item_id)
    cart_item = await database.fetch_one(query)

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if cart_item["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this cart item")

    
    delete_query = cart.delete().where(cart.c.id == cart_item_id)
    await database.execute(delete_query)
    return {"detail": "Cart item removed successfully"}





@app.post("/token", tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = users.select().where(users.c.email == form_data.username)
    user = await database.fetch_one(query)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer"}




def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi