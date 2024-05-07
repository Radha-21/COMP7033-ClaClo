from fastapi import FastAPI, HTTPException, File, UploadFile, Response
from pydantic import BaseModel
from pymongo import MongoClient
import urllib.parse

# MongoDB connection
username = urllib.parse.quote_plus("19280233")
password = urllib.parse.quote_plus("Manthan@1234")
client = MongoClient(f"mongodb+srv://{username}:{password}@comp7033.gnddzok.mongodb.net")
db = client['university_management']
students_collection = db['students']
assignments_collection = db['assignments']
feedback_collection = db['feedback']
teaching_materials_collection = db['teaching_materials']
student_profiles_collection = db['student_profiles']
users_collection = db['users']  # Define users_collection
app = FastAPI()


# Model for student
class Student(BaseModel):
    name: str
    student_id: str
    modules: list[str] = []


# Model for user authentication
class User(BaseModel):
    username: str
    password: str


# Endpoint to signup
@app.post("/signup", tags=["User Authentication"])
async def signup(user: User):
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    else:
        users_collection.insert_one(user.dict())
        return {"message": "User signed up successfully"}


# Endpoint to login
@app.post("/login", tags=["User Authentication"])
async def login(user: User):
    existing_user = users_collection.find_one({"username": user.username, "password": user.password})
    if existing_user:
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    
# Endpoint to view student profile
@app.get("/profile/{student_id}", tags=["Student Profile"])
async def get_student_profile(student_id: str):
    student = students_collection.find_one({"student_id": student_id})
    if student:
        return student
    else:
        raise HTTPException(status_code=404, detail="Student not found")


# Endpoint to create student profile
@app.post("/profile", tags=["Student Profile"])
async def create_student_profile(student: Student):
    existing_student = students_collection.find_one({"student_id": student.student_id})
    if existing_student:
        raise HTTPException(status_code=400, detail="Student profile already exists")
    else:
        students_collection.insert_one(student.dict())
        return {"message": "Student profile created successfully"}


# Endpoint to update student profile
@app.put("/profile/{student_id}", tags=["Student Profile"])
async def update_student_profile(student_id: str, student: Student):
    existing_student = students_collection.find_one({"student_id": student_id})
    if existing_student:
        students_collection.update_one({"student_id": student_id}, {"$set": student.dict()})
        return {"message": "Student profile updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")


# Endpoint to delete student profile
@app.delete("/profile/{student_id}", tags=["Student Profile"])
async def delete_student_profile(student_id: str):
    result = students_collection.delete_one({"student_id": student_id})
    if result.deleted_count > 0:
        return {"message": "Student profile deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")


# Endpoint to enroll in a class
@app.post("/enrol/{student_id}/{module}", tags=["Course Management"])
async def enroll_to_class(student_id: str, module: str):
    student = students_collection.find_one({"student_id": student_id})
    if student:
        if module not in student["modules"]:
            students_collection.update_one({"student_id": student_id}, {"$push": {"modules": module}})
            return {"message": f"Student {student_id} enrolled in module {module} successfully"}
        else:
            return {"message": f"Student {student_id} is already enrolled in module {module}"}
    else:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


# Endpoint to quit from a class
@app.delete("/quit/{student_id}/{module}", tags=["Course Management"])
async def quit_from_class(student_id: str, module: str):
    student = students_collection.find_one({"student_id": student_id})
    if student:
        if module in student["modules"]:
            students_collection.update_one({"student_id": student_id}, {"$pull": {"modules": module}})
            return {"message": f"Student {student_id} quit from module {module} successfully"}
        else:
            return {"message": f"Student {student_id} is not enrolled in module {module}"}
    else:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")


# Endpoint to submit exercises and assessment work
@app.post("/submit_assignment/{student_id}", tags=["Assignment"])
async def submit_assignment(student_id: str, assignment_file: UploadFile = File(...)):
    # Save the submitted assignment file to a designated location or database
    # Here, we'll just print the filename and content
    content = await assignment_file.read()
    print(f"Received assignment file from student {student_id}: {assignment_file.filename}")
    print(f"Content: {content.decode('utf-8')}")
    return {"message": "Assignment submitted successfully"}


# Endpoint to view teacher's feedback
@app.get("/feedback/{student_id}", tags=["Feedback"])
async def view_feedback(student_id: str):
    feedback = feedback_collection.find({"student_id": student_id})
    if feedback:
        return {"feedback": list(feedback)}
    else:
        raise HTTPException(status_code=404, detail=f"No feedback found for student {student_id}")


# Endpoint to view teaching materials
@app.get("/teaching_materials", tags=["Teaching Material"])
async def view_teaching_materials():
    materials = teaching_materials_collection.find({})
    if materials:
        return {"teaching_materials": [material["name"] for material in materials]}
    else:
        raise HTTPException(status_code=404, detail="No teaching materials found")


# Endpoint to download teaching material
@app.get("/teaching_materials/{material_name}", tags=["Teaching Material"])
async def download_teaching_material(material_name: str):
    material = teaching_materials_collection.find_one({"name": material_name})
    if material:
        content = material["content"]
        response = Response(content, media_type='application/octet-stream')
        response.headers["Content-Disposition"] = f"attachment; filename={material_name}"
        return response
    else:
        raise HTTPException(status_code=404, detail="Teaching material not found")
