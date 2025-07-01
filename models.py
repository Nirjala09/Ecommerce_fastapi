from sqlalchemy import Table, Column, Integer, String, Float
from database import metadata
from sqlalchemy import ForeignKey

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), index=True),
    Column("description", String(1000)),
    Column("price", Float),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, index=True),
    Column("hashed_password", String(1000))
)




cart = Table(
    "cart",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id")),
    Column("quantity", Integer)
)
