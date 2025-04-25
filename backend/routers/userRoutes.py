from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from dependencies import get_db
import models
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Annotated 
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from datetime import timedelta, datetime, timezone
from itsdangerous import URLSafeTimedSerializer
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import logging
from starlette.responses import JSONResponse
from jose import JWTError, jwt
import pandas as pd
import string
import random
import secrets
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import BaseDocTemplate, Table, TableStyle, Paragraph, Frame, PageTemplate
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from io import BytesIO
import os
import pytz
import zipfile

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

SECRET_KEY = "test_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

conf = ConnectionConfig(
    MAIL_USERNAME = "readspeak0@gmail.com",
    MAIL_PASSWORD = "cbtwdijyxquetldb",
    MAIL_FROM = "readspeak0@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="ReadSpeak",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

fm = FastMail(conf)

philippine_timezone = pytz.timezone("Asia/Manila")

class UserCreate(BaseModel):
  username: str
  password: str
  email: str
  role: str

class UserResponse(BaseModel):
  user_id: int
  name: str
  email: str
  role: str
  date_created: datetime
  is_verified: bool
  level: Optional[int] = None
  current_stage: Optional[int] = None
  first_login: Optional[bool] = None
  date_verified: Optional[datetime] = None
  gender: Optional[str] = None
  section_id: Optional[int] = None

class StudentCreate(BaseModel):
  username: str
  password: str
  email: str
  level: int
  section: int
  gender: str
  
class SectionCreate(BaseModel):
  section_name: str

class Token(BaseModel):
  access_token: str
  token_type: str

class EmailSchema(BaseModel):
    email: List[EmailStr]
  
class StudentList(BaseModel):
  student_id: int
  student_email: str
  student_name: str
  gender: str
  level_id: Optional[int]
  level_name: Optional[str]
  section_id: int
  total_stages: int
  current_stage: int

class ExcelStudentData(BaseModel):
    name: str
    level: int
    gender: Optional[str] = None
    
class StudentResponse(BaseModel):
    name: str
    email: str
    password: str
    level: int
    gender: Optional[str] = None

# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
#   try:
#     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#     username: str = payload.get('sub')
#     user_id: int = payload.get('id')
#     if username is None or user_id is None:
#       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
#     return {'username': username, 'id': user_id}
#   except JWTError:
#     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
# user_dependency = Annotated[dict, Depends(get_current_user)]

db_dependency = Annotated[Session, Depends(get_db)]

#Auth stuff
@router.post("/register/")
async def register_user(db: db_dependency, create_user_request: UserCreate):
  if db.query(models.User).filter(models.User.email == create_user_request.email).first():
    raise HTTPException(status_code=400, detail='Email already registered')
  
  create_user_model = models.User(
    name = create_user_request.username,
    hashed_password = pwd_context.hash(create_user_request.password),
    email = create_user_request.email,
    role = create_user_request.role,
    date_created = datetime.now(pytz.timezone("Asia/Manila")),
    is_verified = False
  )
  
  db.add(create_user_model)
  db.commit()
  
  token = create_url_safe_token({"email": create_user_request.email})
  #make this dynamic by storing link as variable especially once hosted
#   link = f"http://localhost:8000/verify-email/{token}"
  
#   html_message = f""" 
#   <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Welcome to ReadSpeak</title>
# </head>
# <body style="font-family: Arial, sans-serif; background-color: #f0f4fc; margin: 0; padding: 0; text-align: center;">
#     <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); overflow: hidden; padding: 20px; text-align: center;">
#         <div style="color:#ffffff; background-color: #4CAF50; color: white; padding: 15px; border-top-left-radius: 8px; border-top-right-radius: 8px;">
#             <h1>Welcome to ReadSpeak</h1>
#         </div>
#         <div style="padding: 20px;">
#             <h2>Hello!</h2>
#             <p>Thank you for joining ReadSpeak. We're excited to have you on board!</p>
#             <p>To get verified, please click the button below:</p>
#             <div style="margin: 20px auto;">
#                 <a href="{link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-size: 16px;">Verify Account</a>
#             </div>
#             <p>If you have any questions, feel free to reach out to us!</p>
#         </div>
#         <div style="background-color: #f1f1f1; padding: 10px; color: #777; font-size: 12px; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
#             <p>&copy; 2024 ReadSpeak. All rights reserved.</p>
#         </div>
#     </div>
# </body>
# </html>
#   """

#   message = send_email(recipients=[create_user_request.email], subject="Verify Your Email", body=html_message)
    
#   await fm.send_message(message)
  
  return {"message": "Email sent successfully"}

#token shiz
token_serializer = URLSafeTimedSerializer(
    secret_key="test_key",
    salt="email-verification"
)

def send_email(recipients: list[str], subject: str, body:str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    return message

def create_url_safe_token(data: dict):
    token = token_serializer.dumps(data)
    
    return token

def decode_url_safe_token(token: str):
    try:
        token_data = token_serializer.loads(token)
        
        return token_data
    
    except Exception as e:
        logging.error(str(e))

@router.get("/verify-email/{token}")
async def verify_user_token(token: str, db:db_dependency):
  token_data = decode_url_safe_token(token)
  
  user_email = token_data.get('email')
  
  if user_email:
    user = db.query(models.User).filter(models.User.email == user_email).first()
    
    if not user:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.', headers={"WWW-Authenticate": "Bearer"})
    
    user.is_verified = True
    user.date_verified = datetime.now(timezone.utc)
    db.commit()
    
    return JSONResponse(content = {
      "message": "Account Verified"
    }, status_code=status.HTTP_200_OK,
    )
  return JSONResponse(content={
    "message": "Error occured during verification",
  }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,)
    

@router.post("/login/")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
  user = authenticate_user(form_data.username, form_data.password, db)
  if not user:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.', headers={"WWW-Authenticate": "Bearer"})
  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(data={"sub": user.name, "id":user.user_id, "role": user.role}, expires_delta=access_token_expires)
  # print(f"Authenticated user: {user.__dict__}")
  return {'access_token': access_token, 'user_id': user.user_id, 'role': user.role}
  
def authenticate_user(email: str,  password: str, db: db_dependency):
  user = db.query(models.User).filter(models.User.email == email).first()
  if not user:
    return False
  if not pwd_context.verify(password, user.hashed_password):
    return False
  
  return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(pytz.timezone("Asia/Manila")) + expires_delta
  else:
    expire = datetime.now(pytz.timezone("Asia/Manila")) + timedelta(minutes=15)
  to_encode.update({'exp': expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

@router.get("/verify-token/{token}")
async def verify_user_token(token: str, db: db_dependency):
  verify_token(db, token=token)
  return {"message": "Token is valid"}

def verify_token( db: db_dependency, token: str = Depends(oauth2_scheme)):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise HTTPException(status_code=403, detail="Token is invalid or expired")
    db_token = db.query(models.ExpiredTokens).filter(models.ExpiredTokens.token_string == token).first()
    if db_token:
      raise HTTPException(status_code=403, detail="Token is invalid or expired")
    return payload
  except JWTError:
    raise HTTPException(status_code=403, detail="Token is invalid or expired")

# def create_access_token(username: str, user_id: int, expires_delta: timedelta):
#   encode = {'sub': username, 'id': user_id}
#   expires = datetime.now(timezone.utc) + expires_delta
#   encode.update({'exp': expires})
#   return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/logout/{token}")
async def logout_user(token: str, db: db_dependency):
  try:
    verify_token(db, token=token)
    db_token = models.ExpiredTokens(token_string = token)
    db.add(db_token)
    db.commit()
  except JWTError:
    return token
  

#user funcs
#temporary solution
@router.get("/me/{userId}", response_model=UserResponse)
async def user(userId: int, db: db_dependency):
  result = db.query(models.User).filter(models.User.user_id == userId).first()
  if not result:
    raise HTTPException(status_code=404, detail='User is not found')
  result.date_created = result.date_created.astimezone(philippine_timezone)
  return result

# @router.get("/mev2/")
# async def user2(user: user_dependency, db: db_dependency):
#   if user is None:
#     raise HTTPException(status_code=401, detail='Authentication Failed')
#   return {"User": user}

@router.post("/add/student/")
async def add_student_account(db:db_dependency, user: StudentCreate):
  if db.query(models.User).filter(models.User.email == user.email).first():
    raise HTTPException(status_code=400, detail='Email already registered')
  
  db_stage = db.query(models.Stages).filter(models.Stages.level_requirement == user.level).order_by(models.Stages.stage_sequence).first()
  create_user_model = models.User(
    name = user.username,
    hashed_password = pwd_context.hash(user.password),
    email = user.email,
    role = 'student',
    date_created = datetime.now(pytz.timezone("Asia/Manila")),
    is_verified = False,
    level = user.level,
    section_id = user.section,
    gender = user.gender,
    current_stage = 1,
    first_login = True
  )
  
  db.add(create_user_model)
  db.commit()

@router.get("/download_class_template")
async def download_student_template():

    template_path = "routers/class_list_template.xlsx"  # Path to your template file
    print("Current working directory:", os.getcwd())
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template file not found")

    return FileResponse(
        path=template_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="student_list_template.xlsx" #this is what the client sees as the downloaded file name
    )
  
@router.post("/upload/students/")
async def upload_students(section_id: int, db: db_dependency, file: UploadFile = File(...) ):
  
  if not (file.filename.endswith(".xlsx") or file.filename.endswith(".csv")):
    raise HTTPException(status_code=400, detail="Invalid file type. Only .xslx and .csv files are allowed")
  
  try:
    level_to_id = {
      "Emerging Reader": 1,
      "Developing Reader": 2,
      "Transitioning Reader": 3,
      "Reading at Grade Level": 4
    }
    
    if file.filename.endswith(".xlsx"):
      try:
	df = pd.read_excel(file.file, engine="openpyxl")
      except zipfile.BadZipFile:
	raise HTTPException(
	    status_code=400,
	    detail="The uploaded Excel file is invalid or password protected. Pleas check the file."
	)
      except Exception as e:
	raise HTTPException(
	    status_code=400,
	    detail=f"An error occurred while reading the Excel file: {str(e)}"
	)
    elif file.filename.endswith(".csv"):
      df = pd.read_csv(file.file)
    new_students = []
    for index, row in df.iterrows():
      name = row["Name"]
      level = row["Level"]
      gender = row["Gender"]
      password = str(row["Password"])
        
      if not (password.isdigit() and len(password) == 12):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid password for student '{name}'. Password must be exactly 11 digits."
        )
      
      level_id = level_to_id.get(level, None)
      
      if level_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid level '{level}' for student '{name}'")
      
      email = f"{name.lower().replace(' ','_')}@readspeak.com"
      
      #if duplicate
      if db.query(models.User).filter(models.User.email == email).first():
        email = f"{name.lower().replace(' ', '_')}{secrets.token_hex(2)}@readspeak.com"
        
      db_students = models.User(
        name = name,
        hashed_password=pwd_context.hash(password),
        email=email,
        role='student',
        date_created=datetime.now(pytz.timezone("Asia/Manila")),
        is_verified=False,
        level=level_id,
        gender=gender,
        current_stage=1,
        section_id=section_id,
        first_login = True
      )
      
      db.add(db_students)
      student_response_data = {"name":name, "email":email, "password":password, "level":level, "gender":gender}
      print(f"Student data: {student_response_data}") #Debug print
      new_students.append(StudentResponse(name=name, email=email, password=password, level=level_id, gender=gender))
      
    db.commit()

    output = BytesIO()
    frame_table = Frame(50, 50, letter[0] - 100, letter[1] - 150)

    def add_footer(canvas, doc):
      canvas.saveState()
      canvas.setFont('Times-Roman', 10)
      text_width = stringWidth(notice_text, 'Times-Roman', 10)
      canvas.drawString((letter[0] - text_width) / 2.0, 20, notice_text) # corrected line
      canvas.restoreState()

    page_template = PageTemplate('myTemplate', frames=[frame_table], onPage=add_footer)
    doc = BaseDocTemplate(output, pagesize=letter, pageTemplates=page_template)
    data = [["Name", "Email", "Password"]]
    for student in new_students:
      data.append([student.name, student.email, student.password])
    table = Table(data)
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTSIZE', (0, 1), (-1, -1), 12)])
    table.setStyle(style)
    
    styles = getSampleStyleSheet()
    notice_style = styles['Normal']
    notice_style.alignment = 1  # Center alignment
    generation_date = datetime.now(pytz.timezone("Asia/Manila")).strftime("%B %d, %Y, %H:%M %p")
    notice_text = f"Generation Notice: This report was automatically generated by the ReadSpeak system on {generation_date}."
    notice = Paragraph(notice_text, notice_style)
    
    elements = [table]
    

    doc.build(elements)

    headers = {'Content-Disposition': 'attachment; filename=student_credentials.pdf'}
    return Response(
          content=output.getvalue(),
          media_type="application/pdf",
          headers=headers
    )
  except HTTPException as http_exc:
    raise http_exc
  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# def generate_easy_password(length=8):
#     characters = string.ascii_lowercase + string.digits
#     return ''.join(random.choice(characters) for i in range(length))

# @router.get("/download/pdf/")
# async def download_pdf(students: List[StudentResponse]):
#   output = StringIO()
#   doc = SimpleDocTemplate(output, pagesize=letter)
#   data = [["Name", "Email", "Password"]]
#   for student in students:
#     data.append([student.name, student.email, student.password])

#   table = Table(data)
#   style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)])
#   table.setStyle(style)
#   elements = [table]
#   doc.build(elements)
#   headers = {'Content-Disposition': 'attachment; filename=student_credentials.pdf'}
#   return Response(
#         content=output.getvalue(),
#         media_type="application/pdf",
#         headers=headers
#   )

@router.put("/tutorialfinish/{userId}")
async def user_finish_tutorial(userId: int, db: db_dependency):
  result = db.query(models.User).filter(models.User.user_id == userId).first()
  if not result:
    raise HTTPException(status_code=404, detail='User is not found')
  
  result.first_login = False
  db.commit()
  return("Tutorial finished")

@router.post("/add/section")
async def add_section(db: db_dependency, section: SectionCreate):
  db_section = models.Sections(
    section_name = section.section_name
  )
  
  db.add(db_section)
  db.commit()
  
@router.put("/delete/section/{sectionId}")
async def delete_section(sectionId: int,db: db_dependency):
  db_section = db.query(models.Sections).filter(models.Sections.section_id == sectionId).first()
  if not db_section:
    raise HTTPException(status_code=404, detail='Section is not found')
  # db_users = db.query(models.User).filter(models.User.section_id == sectionId).all()
  # for users in db_users:
  #   db.delete(users)
  db.delete(db_section) 
  db.commit()
  
@router.put("/delete/{userId}")
async def delete_student(userId: int, db: db_dependency):
    try:
        student = db.query(models.User).filter(models.User.user_id == userId).first()
        if not student:
            raise HTTPException(status_code=404, detail='Student not found')

        # Delete related history entries
        db.query(models.AssessmentHistory).filter(models.AssessmentHistory.student_id == userId).delete()
        db.query(models.ComprehensionAssessmentHistory).filter(models.ComprehensionAssessmentHistory.student_id == userId).delete()

        # Delete the student
        db.delete(student)
        db.commit()

        return {"message": "Student and related history deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
  
@router.get("/sections/")
async def get_sections(db:db_dependency):
  db_sections = db.query(models.Sections).all()
  if not db_sections:
    raise HTTPException(status_code=404, detail='Students is not found') 
  return db_sections

@router.get("/students/{section_id}")
async def get_students(section_id:int,db:db_dependency):
  students = db.query(models.User).filter(models.User.role == 'student', models.User.section_id == section_id).all()
  if not students:
    raise HTTPException(status_code=404, detail='Students is not found') 
  result = []
  for student in students:
    level = db.query(models.PronunciationAssessmentType).join(models.User).filter(models.User.level == student.level).first()
    if not level:
      raise HTTPException(status_code=404, detail=f"Level not found for student {student.user_id}")
    total_stages = db.query(models.Stages).filter(models.Stages.level_requirement == level.type_id).count()
    current_stage = student.current_stage-1 if student.current_stage is not None else 0
    result.append(StudentList(student_id=student.user_id, student_email=student.email, student_name=student.name, gender=student.gender, level_id=level.type_id, level_name=level.type_name, section_id=student.section_id, total_stages=total_stages, current_stage=current_stage))
  return result

@router.get("/students/")
async def get_students(db:db_dependency):
  students = db.query(models.User).filter(models.User.role == 'student').all()
  if not students:
    raise HTTPException(status_code=404, detail='Students is not found') 
  result = []
  for student in students:
    level = db.query(models.PronunciationAssessmentType).join(models.User).filter(models.User.level == student.level).first()
    if not level:
      raise HTTPException(status_code=404, detail=f"Level not found for student {student.user_id}")
    total_stages = db.query(models.Stages).filter(models.Stages.level_requirement == level.type_id).count()
    current_stage = student.current_stage-1 if student.current_stage is not None else 0
    result.append(StudentList(student_id=student.user_id, student_email=student.email, student_name=student.name, gender=student.gender, level_id=level.type_id, level_name=level.type_name, section_id=student.section_id, total_stages=total_stages, current_stage=current_stage))
  return result
