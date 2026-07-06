from pymongo import MongoClient

uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)

db = client["college"]
students = db["students"]
students.delete_one({"roll_no": 104})

print("Student Deleted Successfully!")