from contextlib import asynccontextmanager
from typing import Annotated, Union, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from routers import auth, users
from fastapi.middleware.cors import CORSMiddleware
from services.auth import oauth2_scheme


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


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


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
