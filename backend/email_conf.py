from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
from itsdangerous import URLSafeTimedSerializer
import logging

class EmailSchema(BaseModel):
    addresses: List[str]


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

app = FastAPI()

fm = FastMail(conf)

@app.post("/email")
async def simple_send(email: EmailSchema):
    email = email.addresses
    
    html = "<h1> Welcome to the app test </h1>"
    
    message = send_email(recipients=email, subject="Welcome", body=html)
    
    await fm.send_message(message)
    
    return {"message": "Email sent successfully"}

def send_email(recipients: list[str], subject: str, body:str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    return message

token_serializer = URLSafeTimedSerializer(
    secret_key="test_key",
    salt="email-verification"
)

def create_url_safe_token(data: dict):
    token = token_serializer.dumps(data)
    
    return token

def decode_url_safe_token(token: str):
    try:
        token_data = token_serializer.loads(token)
        
        return token_data
    
    except Exception as e:
        logging.error(str(e))
    
if __name__ == "__main__":
  import uvicorn
  
  uvicorn.run(app, host="0.0.0.0", port=8000)