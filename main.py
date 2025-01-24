from dbos import DBOS
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()
DBOS(fastapi=app)


@DBOS.step()
def step_one():
    print("Step one completed!")


@DBOS.step()
def step_two():
    print("Step two completed!")


@DBOS.workflow()
def dbos_workflow():
    step_one()
    for _ in range(5):
        print("Press Control + \ to stop the app...")
        DBOS.sleep(1)
    step_two()


@app.get("/")
def fastapi_endpoint():
    dbos_workflow()
    return JSONResponse(content={"message": "Hello, World!"})
