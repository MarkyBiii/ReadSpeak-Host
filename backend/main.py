from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
import cloudinary
import cloudinary.uploader
from routers import assessmentRoutes, stagesRoutes, submissionRoutes, userRoutes, statRoutes

#API Stuff
app = FastAPI()
models.Base.metadata.create_all(bind=engine)
#Comment/change these out when deploying
origins = ["http://127.0.0.1:3000/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# cloudinary.config( 
#     cloud_name = "dxijt2kwv", 
#     api_key = "219654775259177", 
#     api_secret = "iDtYiBSPmAx8ZE5DMxtTNS8s_zQ", # Click 'View API Keys' above to copy your API secret
#     secure=True
# )

cloudinary.config( 
    cloud_name = "dxmjz8dkp", 
    api_key = "985598938874758", 
    api_secret = "U-RKTi_wPw6uOjayoF8gZGDQG24", # Click 'View API Keys' above to copy your API secret
    secure=True
)

#api endpoints
app.include_router(assessmentRoutes.router)
app.include_router(stagesRoutes.router)
app.include_router(submissionRoutes.router)
app.include_router(userRoutes.router)
app.include_router(statRoutes.router)
@app.get("/")
async def root():
  return{"detail" : "API is running."}

if __name__ == "__main__":
  import uvicorn
  
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)