from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from typing import Annotated, Union, Optional
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, requests
from fastapi.responses import JSONResponse
from sqlmodel import Field, Session, SQLModel, select
from app.routers import auth, users, jobs
from fastapi.middleware.cors import CORSMiddleware
from app.services.auth import oauth2_scheme
from app.models.user import User
from app.models.job import Job
from app.database import engine
from roboflow import Roboflow

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
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: Union[int, None] = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: Union[int, None] = Field(default=None, primary_key=True)
    secret_name: str


class HeroPublic(HeroBase):
    id: int

class HeroCreate(HeroBase):
    secret_name: str

class HeroUpdate(HeroBase):
    name: Union[str, None] = None
    age: Union[int, None] = None
    secret_name: Union[str, None] = None


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

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    Accepts an image file, sends it to Roboflow for prediction, and returns the prediction JSON.
    """
    try:
        # Validate the file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file is not an image.")

        # Save the uploaded image temporarily
        temp_image_path = f"temp_{image.filename}"
        with open(temp_image_path, "wb") as buffer:
            buffer.write(await image.read())

        # Perform inference using Roboflow SDK
        predictions = model.predict(temp_image_path, confidence=7, overlap=50).json()

        # Clean up temporary image
        os.remove(temp_image_path)

        # Return the prediction JSON
        return JSONResponse(content=predictions)

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=str(e))

# Get heroes
@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep, # Dependency injection
    offset: int = 0, # the number of records to skip before starting to return results
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero)
                          .offset(offset)
                          .limit(limit)).all()
    return heroes

# Get a hero by ID
@app.get("/heroes/{hero_id}")
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

# Create a hero
@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero) # to add the new hero instance to the database session
    session.commit() # to add the new hero instance to the database session
    session.refresh(db_hero) # to refresh the instance with the data from the database
    return db_hero

# Update a hero
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    # excluding any values that would be there just for being the default values. 
    # To do it we use exclude_unset=True. This is the main trick. 🪄
    hero_db.sqlmodel_update(hero_data)

    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db

# Delete a hero
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}


@app.get("/")
async def root():
    return {"message": "Hello World"}
