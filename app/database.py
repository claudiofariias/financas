import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["finance_db"]

saldo_collection = db["saldo"]
users_collection = db["users"]