from pymongo import MongoClient

uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)

db = client["college"]
students = db["students"]

students.update_one(
    {"roll_no": 102},
    {"$set": {"course": "AI & Data Science"}}
)

print("Student Updated Successfully!")