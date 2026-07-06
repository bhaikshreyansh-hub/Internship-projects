from pymongo import MongoClient
import random

uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)

db = client["college"]
students = db["students"]

first_names = [
    "Rahul", "Priya", "Amit", "Sneha", "Rohan",
    "Anjali", "Karan", "Neha", "Vikas", "Pooja"
]

last_names = [
    "Sharma", "Patel", "Verma", "Iyer", "Gupta",
    "Singh", "Joshi", "Mehta", "Kulkarni", "Jain"
]

courses = [
    "Data Science & Engineering",
    "Computer Engineering",
    "Information Technology",
    "Artificial Intelligence",
    "Cyber Security"
]

subjects_pool = [
    "Python", "MongoDB", "SQL", "Java",
    "Machine Learning", "Cloud Computing",
    "DBMS", "Operating Systems"
]

skills_pool = [
    "Python", "Java", "SQL",
    "Problem Solving", "Communication",
    "Leadership", "Data Analysis"
]

cities = [
    "Panvel", "Mumbai", "Pune",
    "Nagpur", "Navi Mumbai"
]

student_list = []

for i in range(1, 501):
    student = {
        "student_id": 1000 + i,
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "age": random.randint(18, 24),
        "gender": random.choice(["Male", "Female"]),
        "email": f"student{i}@example.com",
        "phone": f"98{random.randint(10000000,99999999)}",
        "course": random.choice(courses),
        "semester": random.randint(1, 8),
        "cgpa": round(random.uniform(6.0, 9.8), 2),
        "subjects": random.sample(subjects_pool, 4),
        "skills": random.sample(skills_pool, 3),
        "address": {
            "city": random.choice(cities),
            "state": "Maharashtra"
        }
    }

    student_list.append(student)

students.insert_many(student_list)

print("500 students inserted successfully!")