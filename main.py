from fastapi import FastAPI, Request, UploadFile, Form
import pandas as pd
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

master_file_uploaded = None
master_file_name = None
master_matrix_dataframe = None

eid_file_uploaded = None
eid_file_name = None
eid_dataframe = None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})


@app.post("/", response_class=HTMLResponse)
async def index(request: Request,
                master_file: UploadFile | None = None,
                eid_file: UploadFile | None = None,
                eid: str = Form(default=None),
                oid: str = Form(default=None),
                env: str = Form(default=None)):
    form = await request.form()
    global master_file_uploaded, master_file_name
    
    if "master-submit" in form.keys():
        master_file_name = master_file.filename
        master_error = get_master_matrix(master_file)
        return templates.TemplateResponse("index.html", context={"request": request,
                                                                "master_file_name": master_file_name,
                                                                "master_error": master_error,
                                                                "master_file_uploaded": master_file_uploaded})
    if "eid-sheet-submit" in form.keys():
        eid_file_name = eid_file.filename
        eid_error = get_eid_sheet(eid_file)
        return templates.TemplateResponse("index.html", context={"request": request,
                                                                "eid_file_name": eid_file_name,
                                                                "eid_error": eid_error,
                                                                "eid_file_uploaded": eid_file_uploaded})
        
    if "eid-submit" in form.keys():
        print(f"Search with eid: {eid}")
        final = from_eid(eid.upper())
        return templates.TemplateResponse("index.html", context={"request": request, "master_file_uploaded": master_file_uploaded, "master_file_name": master_file_name, "final": final})

    if "oid-submit" in form.keys():
        print(f"Search with oid: {oid} and env: {env}")
        
        return templates.TemplateResponse("index.html", context={"request": request, "master_file_uploaded": master_file_uploaded, "master_file_name": master_file_name})


def get_master_matrix(master_matrix_path):
    """
    get_master_matrix - Uploads the Master Matrix file supplied and creates a Pandas DataFrame.

    Uploads the Master Matrix file supplied and creates a Pandas DataFrame, also throws exceptions if the file format is not excel (.xlsx)
    """
    global master_file_uploaded, master_matrix_dataframe
    
    read_cols = ['Corp', 'CONCATENATE', 'RESI EID', 'Market', 'Altice One']
    try:
        master_matrix_dataframe = pd.read_excel(master_matrix_path.file, usecols=read_cols, converters={'Corp':str, 'CONCATENATE': str})
    except ImportError as e:
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
        master_file_uploaded = True
        return None


def get_eid_sheet(eid_path) -> None:
    """
    get_eid_sheet - Uploads the EID file supplied and creates a Pandas DataFrame.

    Uploads the EID file supplied and creates a Pandas DataFrame, also throws exceptions if the file format is not excel (.xlsx)
    """

    global eid_file_uploaded, eid_dataframe

    try:
        eid_dataframe = pd.read_excel(eid_path.file, usecols=['ELIGIBILITY_ID', 'OFFER_ID'], converters={'ELIGIBILITY_ID': str, 'OFFER_ID': str})
    except ImportError as e:
        return e
    except FileNotFoundError:
        pass
    except ValueError as e:
        if "Excel file format cannot be determined, you must specify an engine manually" in e.args[0]:
            return "Please upload an excel file only!"
        elif "Usecols do not match columns, columns expected but not found" in e.args[0]:
            error_column_name = str(e)[str(e).index("'"):].replace(']', '')
            return f"Column(s) {error_column_name} not found."
    else:
        eid_file_uploaded = True
        return None


def from_eid(eid: str) -> None:
    """
    from_eid - Displays Corp and Ftax combination for provided EID value.

    Displays the Corp and Ftax combination for a provided EID.

    :param eid: EID to check the Corp-Ftax combination.
    :type eid: str
    """
    corp_ftax = []
    for i in master_matrix_dataframe.index:
        if master_matrix_dataframe['RESI EID'][i] == eid:
            a = f"""{master_matrix_dataframe['CONCATENATE'][i][:4]}-{master_matrix_dataframe['CONCATENATE'][i][4:]} - {master_matrix_dataframe['Market'][i].strip()}"""
            corp_ftax.append(a)
            
    if corp_ftax:
        final = [corp_ftax[x:x+4] for x in range(0, len(corp_ftax)-1, 4)]
        final_df = pd.DataFrame(final).to_html(classes=["table", "table-dark", "table-striped", "table-bordered"], index=False, justify="center", header=False).replace('<td>', '<td class="text-center">')
    else:
        final_df = '<small class="text-danger">Invalid EID, try again.</small>'
    return final_df