# database.py

from sqlalchemy import create_engine, MetaData
from databases import Database

DATABASE_URL = "mysql+aiomysql://root:%40Check123@localhost/ecommerce"

 

database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"))
