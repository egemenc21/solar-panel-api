from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from typing import Annotated, Union, Optional
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, requests
from fastapi.responses import JSONResponse
from sqlmodel import Field, Session, SQLModel, select
from app.routers import auth, users, jobs, fields, panel_images
from fastapi.middleware.cors import CORSMiddleware
from app.services.auth import oauth2_scheme, get_current_active_user
# from app.models.user import User
# from app.models.job import Job
from app.models.models import User, Job, SolarField, PanelImage
from app.database import engine, create_engine
from roboflow import Roboflow
from PIL import Image, ImageDraw, ImageFont
from fastapi.staticfiles import StaticFiles

# Load environment variables from the .env file
load_dotenv()
# Access environment variables
API_KEY = os.getenv("API_KEY")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT")
VERSION = os.getenv("VERSION")

# Initialize Roboflow
rf = Roboflow(api_key=API_KEY)
project = rf.workspace().project(MODEL_ENDPOINT)
model = project.version(VERSION).model

# Table = true tablo oluşturulmasını sağlar
# Field(primary_key=True) tells SQLModel that the id is the primary key in the SQL database
# Field(index=True) tells SQLModel to create an index for the name and age columns, that would allow
# faster lookups in the database when reading data filtered by this column.


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlatıldığında çalışacak kod
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# origins = [
#     "http://localhost.tiangolo.com",
#     "https://localhost.tiangolo.com",
#     "http://localhost",
#     "http://localhost:8080",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(fields.router, prefix="/fields", tags=["fields"])
app.include_router(panel_images.router,
                   prefix="/panel_images", tags=["panel_images"])
app.mount("/classified_images",
          StaticFiles(directory="classified_images"), name="classified_images")


@app.post("/predict")
async def predict(
    current_user: Annotated[User, Depends(get_current_active_user)], 
    session: SessionDep, 
    image: UploadFile = File(...), 
    user_id: int = 0, 
    field_id: int = 0
    ):
    """
    Accepts an image file, sends it to Roboflow for prediction, annotates the image, and saves it.
    """
    try:
        # Validate the file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="Uploaded file is not an image.")

        # Save the uploaded image temporarily
        temp_image_path = f"temp_{image.filename}"
        with open(temp_image_path, "wb") as buffer:
            buffer.write(await image.read())

        # Perform inference using Roboflow SDK
        predictions = model.predict(
            temp_image_path, confidence=7, overlap=50).json()

        # Open the image using PIL for annotation
        pil_image = Image.open(temp_image_path)
        draw = ImageDraw.Draw(pil_image)

        # Define font for labels
        # Use default font
        font = ImageFont.load_default()
        font.size = 20

        # Annotate the image with predictions
        for prediction in predictions.get("predictions", []):
            x, y = prediction["x"], prediction["y"]
            width, height = prediction["width"], prediction["height"]
            label = prediction["class"]

            # Draw a rectangle around the object with smaller line width
            top_left = (x - width // 2, y - height // 2)
            bottom_right = (x + width // 2, y + height // 2)
            draw.rectangle([top_left, bottom_right], outline="red", width=1)

            padding = 15  # Adjust padding value as needed
            # Adjust text position and size
            # Place text slightly above the box
            text_position = (top_left[0], top_left[1] - padding)
            draw.text(text_position, label, fill="red", font=font)

        # Save the annotated image
        filename = f"classified_{image.filename}"
        classified_image_path = save_classified_image(
            pil_image, user_id, filename)

        # Ensure the field exists in the database
        field = session.get(SolarField, field_id)
        if not field:
            raise HTTPException(
                status_code=404, detail=f"SolarField with ID {field_id} not found"
            )

        # Create a new PanelImage instance for each prediction
        for prediction in predictions.get("predictions", []):
            image_class = prediction["class"].lower()  # e.g., 'clean', 'dusty'
            panel_image = PanelImage(
                path=classified_image_path,
                field_id=field_id,
                image_class=image_class,
            )
            session.add(panel_image)

        # Commit the changes
        session.commit()

        # Clean up temporary image
        os.remove(temp_image_path)

        # Return the prediction JSON along with the path to the classified image
        return JSONResponse(content={
            "predictions": predictions,
            "classified_image_path": classified_image_path
        })

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=str(e))


def save_classified_image(image: Image, user_id: int, filename: str) -> str:
    """
    Saves the classified image to a user-specific directory.
    """
    base_dir = "classified_images"
    user_dir = os.path.join(base_dir, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    image_path = os.path.join(user_dir, filename)
    image.save(image_path, "JPEG", quality=85)  # Compress image
    return image_path


@app.get("/")
async def root():
    return {"message": "Hello World"}
