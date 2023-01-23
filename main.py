from fastapi import FastAPI, Request, UploadFile, Form
import pandas as pd
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})


@app.post("/", response_class=HTMLResponse)
async def index(request: Request, file: UploadFile | None = None, eid: str = Form(default=None), oid: str = Form(default=None), env: str = Form(default=None)):
    form = await request.form()
    print(form)
    global file_uploaded
    if "master-submit" in form.keys():
        file_name = file.filename
        error = get_master_matrix(file)
        return templates.TemplateResponse("index.html", context={"request": request,
                                                                "file_name": file_name,
                                                                "error": error,
                                                                "file_uploaded": file_uploaded})
    if "eid-submit" in form.keys():
        print(f"Search with eid: {eid}")
        return templates.TemplateResponse("index.html", context={"request": request, "file_uploaded": file_uploaded})

    if "oid-submit" in form.keys():
        print(f"Search with oid: {oid} and env: {env}")
        return templates.TemplateResponse("index.html", context={"request": request, "file_uploaded": file_uploaded})

file_uploaded = None

def get_master_matrix(master_matrix_path):
    """
    get_master_matrix - Uploads the Master Matrix file supplied and creates a Pandas DataFrame.

    Uploads the Master Matrix file supplied and creates a Pandas DataFrame, also throws exceptions if the file format is not excel (.xlsx)
    """
    global file_uploaded
    
    read_cols = ['Corp', 'CONCATENATE', 'RESI EID', 'Market', 'Altice One']
    try:
        master_matrix_dataframe = pd.read_excel(master_matrix_path.file, usecols=read_cols, converters={'Corp':str, 'CONCATENATE': str})
    except ImportError as e:
        print(e)
        return e
    except FileNotFoundError:
        pass
    except ValueError as e:
        if "Excel file format cannot be determined, you must specify an engine manually" in e.args[0]:
            print("Please upload an excel file only!")
            return "Please upload an excel file only!"
        elif "Usecols do not match columns, columns expected but not found" in e.args[0]:
            error_column_name = str(e)[str(e).index("'"):].replace(']', '')
            print(f"Column(s) {error_column_name} not found.")
            return f"Column(s) {error_column_name} not found."
    else:
        file_uploaded = True
        return None