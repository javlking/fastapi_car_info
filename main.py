from fastapi import FastAPI, Query, Path, HTTPException, status, Body, Request, Form
from fastapi.encoders import jsonable_encoder

from starlette.responses import HTMLResponse, RedirectResponse

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from database import cars

# create an objet to connect templates to our project
templates = Jinja2Templates(directory='templates')


# Create car's models
class Car(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year: int = Field(..., ge=1978, lt=2023)
    price: Optional[float]
    engine: Optional[str] = 'V4'
    autonomous: Optional[bool]
    sold: Optional[List[str]]


# Generate an object to work with api
app = FastAPI()

# Connect staticfiles(mount) it to our project
app.mount('/static', StaticFiles(directory='static'), name='static')


# Create a decorator to make functions
@app.get("/", response_class=RedirectResponse)
def home(request: Request):
    # rendering templates by using TemplateResponse() method of templates object
    return RedirectResponse(url="/cars")


# Get the list of cars
@app.get("/cars", response_class=HTMLResponse)
def get_cars(request: Request,
             number: Optional[str] = Query('10', max_length=3)):  # make a query request by default shows 10 cars
    response = []

    for key, car in list(cars.items())[:int(number)]:
        response.append((key, car))

    return templates.TemplateResponse('home.html', {'request': request, 'cars': response})


# Search the car and redirect it to the api
@app.post("/search", response_class=RedirectResponse)
def search_the_car(id: str = Form(...)):
    return RedirectResponse(f"/cars/{id}", status_code=status.HTTP_302_FOUND)


# Get car by its id
@app.get("/cars/{key}", response_class=HTMLResponse)
def get_car_by_id(request: Request, key: int = Path(..., ge=0, lt=1000)):
    car = cars.get(key)
    response = templates.TemplateResponse('search.html', {'request': request, 'car': car, 'id': key})

    # if program can't find car id, rise No car with this id
    if not car:
        response.status_code = status.HTTP_404_NOT_FOUND

    return response


# Create new cars
@app.post("/create_car", status_code=status.HTTP_201_CREATED)
def create_car(
        make: Optional[str] = Form(...),
        model: Optional[str] = Form(...),
        year: Optional[int] = Form(...),
        price: Optional[float] = Form(...),
        engine: Optional[str] = Form(...),
        autonomous: Optional[bool] = Form(...),
        sold: Optional[List[str]] = Form(None),
        min_id: Optional[int] = Body(0)):

    new_car = [Car(make=make, model=model, year=year, price=price, engine=engine, autonomous=autonomous, sold=sold)]
    # If user don't pass anything rise error
    if len(new_car) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Specify new cars')

    min_id = len(cars.values()) + min_id
    for car in new_car:
        # While cars id exists increment min_id
        while cars.get(min_id):
            min_id += 1

        cars[min_id] = car
        min_id += 1
    return RedirectResponse(url='/', status_code=302)


@app.get('/create', response_class=HTMLResponse)
def add_car(request: Request):
    return templates.TemplateResponse('create_car.html', {'request': request})


# Value updating path
@app.post("/cars/{id}")
def change_info(
        id: int,
        make: Optional[str] = Form(None),
        model: Optional[str] = Form(None),
        year: Optional[int] = Form(None),
        price: Optional[float] = Form(None),
        engine: Optional[str] = Form(None),
        autonomous: Optional[bool] = Form(None),
        sold: Optional[List[str]] = Form(None)):
    stored = cars.get(id)

    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='There was not any car with this ID.')

    # stored variable stores all data from dict stored ^
    stored = Car(**dict(stored))
    car = Car(make=make, model=model, year=year, price=price, engine=engine, autonomous=autonomous, sold=sold)
    new_info = car.dict(exclude_unset=True)

    # Makes a copy of stored with some changes
    new_info = stored.copy(update=new_info)

    # jsonable_encoder makes it possible to parse model to dict
    cars[id] = jsonable_encoder(new_info)
    response = {}
    response[id] = cars[id]

    return RedirectResponse(url='/cars', status_code=302)


@app.get('/edit', response_class=HTMLResponse)
def edit_the_car(request: Request, id: int = Query(...)):
    get_car = cars.get(id)

    if not get_car:
        return templates.TemplateResponse('search.html', {'request': request, 'car': get_car}, status_code=status.HTTP_404_NOT_FOUND)

    return templates.TemplateResponse('edit_car.html', {'request': request,
                                                        'car': get_car,
                                                        'id': id})


# Delete path
@app.get('/delete')
def delete_car_from_frontend(request: Request, id: int = Query(...)):
    get_car = cars.get(id)

    if not get_car:
        return templates.TemplateResponse('search.html', {'request': request, 'car': get_car}, status_code=status.HTTP_404_NOT_FOUND)

    del cars[id] # delete car from dict

    return RedirectResponse(url='/cars', status_code=302)


# For CRUD
@app.delete("/cars/{id}")
def delete_car(id: int):
    stored = cars.get(id)

    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Car to delete not found')

    deleted = Car(**stored)
    del cars[id]

    return f'{deleted} car has successfully deleted'
