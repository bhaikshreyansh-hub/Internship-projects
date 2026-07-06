from pymongo import MongoClient

uri = uri = "mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)

db = client["college"]
students = db["students"]

students.insert_many([
    {
        "student_id": 101,
        "name": "Shreyansh Bhaik",
        "age": 20,
        "gender": "Male",
        "email": "shreyansh.bhaik@example.com",
        "phone": "9876543210",
        "course": "Data Science & Engineering",
        "semester": 5,
        "cgpa": 7.45,
        "subjects": ["Python", "MongoDB", "SQL", "Java"],
        "skills": ["Data Analysis", "Problem Solving", "Communication"],
        "address": {
            "city": "Panvel",
            "state": "Maharashtra"
        }
    },
    {
        "student_id": 102,
        "name": "Rahul Sharma",
        "age": 21,
        "gender": "Male",
        "email": "rahul.sharma@example.com",
        "phone": "9876543211",
        "course": "Computer Engineering",
        "semester": 6,
        "cgpa": 8.20,
        "subjects": ["Java", "DBMS", "Operating Systems", "Networks"],
        "skills": ["Java", "Teamwork", "Leadership"],
        "address": {
            "city": "Mumbai",
            "state": "Maharashtra"
        }
    },
    {
        "student_id": 103,
        "name": "Priya Patel",
        "age": 20,
        "gender": "Female",
        "email": "priya.patel@example.com",
        "phone": "9876543212",
        "course": "Information Technology",
        "semester": 5,
        "cgpa": 8.75,
        "subjects": ["Web Development", "Python", "Cloud Computing"],
        "skills": ["HTML", "CSS", "JavaScript", "Python"],
        "address": {
            "city": "Pune",
            "state": "Maharashtra"
        }
    },
    {
        "student_id": 104,
        "name": "Amit Verma",
        "age": 22,
        "gender": "Male",
        "email": "amit.verma@example.com",
        "phone": "9876543213",
        "course": "Artificial Intelligence",
        "semester": 7,
        "cgpa": 8.90,
        "subjects": ["Machine Learning", "Deep Learning", "Statistics"],
        "skills": ["Python", "TensorFlow", "Data Visualization"],
        "address": {
            "city": "Nagpur",
            "state": "Maharashtra"
        }
    },
    {
        "student_id": 105,
        "name": "Sneha Iyer",
        "age": 21,
        "gender": "Female",
        "email": "sneha.iyer@example.com",
        "phone": "9876543214",
        "course": "Cyber Security",
        "semester": 6,
        "cgpa": 9.10,
        "subjects": ["Network Security", "Cryptography", "Ethical Hacking"],
        "skills": ["Linux", "Networking", "Cyber Security"],
        "address": {
            "city": "Navi Mumbai",
            "state": "Maharashtra"
        }
    }
])

print("5 students inserted successfully!")