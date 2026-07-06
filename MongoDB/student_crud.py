from pymongo import MongoClient

# Replace with your MongoDB Atlas connection string
uri = uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"

# Connect to MongoDB
client = MongoClient(uri)

# Create/Open Database
db = client["college"]

# Create/Open Collection
students = db["students"]

print("Connected to MongoDB successfully!")

# Insert a sample student
student = {
    "roll_no": 101,
    "name": "Shreyansh",
    "age": 20,
    "course": "DSE"
}

result = students.insert_one(student)

print("Student inserted!")
print("Inserted ID:", result.inserted_id)
students.insert_many([
    {
        "roll_no": 102,
        "name": "Rahul",
        "age": 21,
        "course": "Computer Engineering"
    },
    {
        "roll_no": 103,
        "name": "Priya",
        "age": 20,
        "course": "Data Science"
    },
    {
        "roll_no": 104,
        "name": "Amit",
        "age": 22,
        "course": "Information Technology"
    }
])
for student in students.find():
    print(student)