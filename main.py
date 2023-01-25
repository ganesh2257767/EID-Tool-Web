from fastapi import FastAPI, Request, UploadFile, Form
import pandas as pd
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Union
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

master_file_uploaded = None
master_file_name = None
master_matrix_dataframe = None

eid_file_uploaded = None
eid_file_name = None
eid_dataframe = None

eid_tab = "active"
oid_tab = ""
eid_tab_show = "show"
oid_tab_show = ""

final_oid_result = None
final_eid_result = None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", context={"request": request})


@app.post("/", response_class=HTMLResponse)
async def index(
    request: Request,
    master_file: Union[UploadFile, None] = None,
    eid_file: Union[UploadFile, None] = None,
    eid: str = Form(default=None),
    oid: str = Form(default=None),
    env: str = Form(default=None),
):
    form = await request.form()
    global master_file_uploaded, master_file_name, eid_tab, oid_tab, eid_file_name, eid_file_uploaded, final_oid_result, final_eid_result

    if "master-submit" in form.keys():
        eid_tab = "active"
        oid_tab = ""
        eid_tab_show = "show"
        oid_tab_show = ""
        master_file_name = master_file.filename
        master_error = get_master_matrix(master_file)
        return templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "master_file_name": master_file_name,
                "master_error": master_error,
                "master_file_uploaded": master_file_uploaded,
                "eid_tab": eid_tab,
                "oid_tab": oid_tab,
                "eid_tab_show": eid_tab_show,
                "oid_tab_show": oid_tab_show,
            },
        )
    if "eid-sheet-submit" in form.keys():
        eid_file_name = eid_file.filename
        eid_error = get_eid_sheet(eid_file)
        eid_tab = ""
        oid_tab = "active"
        eid_tab_show = ""
        oid_tab_show = "show"
        return templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "eid_file_name": eid_file_name,
                "eid_error": eid_error,
                "eid_file_uploaded": eid_file_uploaded,
                "master_file_uploaded": master_file_uploaded,
                "master_file_name": master_file_name,
                "eid_tab": eid_tab,
                "oid_tab": oid_tab,
                "eid_tab_show": eid_tab_show,
                "oid_tab_show": oid_tab_show,
                "final_eid_result": final_eid_result,
            },
        )

    if "eid-submit" in form.keys():
        eid_tab = "active"
        oid_tab = ""
        eid_tab_show = "show"
        oid_tab_show = ""
        final_eid_result = from_eid(eid.upper())
        return templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "master_file_uploaded": master_file_uploaded,
                "master_file_name": master_file_name,
                "final_eid_result": final_eid_result,
                "eid_tab": eid_tab,
                "oid_tab": oid_tab,
                "eid_tab_show": eid_tab_show,
                "oid_tab_show": oid_tab_show,
                "final_oid_result": final_oid_result,
                "eid_file_name": eid_file_name,
                "eid_file_uploaded": eid_file_uploaded,
            },
        )

    if "oid-submit" in form.keys():
        final_oid_result, display_table = get_corp_ftax_from_offer_id(env, oid)
        eid_tab = ""
        oid_tab = "active"
        eid_tab_show = ""
        oid_tab_show = "show"
        return templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "master_file_uploaded": master_file_uploaded,
                "master_file_name": master_file_name,
                "eid_tab": eid_tab,
                "oid_tab": oid_tab,
                "eid_tab_show": eid_tab_show,
                "oid_tab_show": oid_tab_show,
                "eid_file_name": eid_file_name,
                "eid_file_uploaded": eid_file_uploaded,
                "final_oid_result": final_oid_result,
                "final_eid_result": final_eid_result,
                "display_table": display_table
            },
        )


def get_master_matrix(master_matrix_path):
    """
    get_master_matrix - Uploads the Master Matrix file supplied and creates a Pandas DataFrame.

    Uploads the Master Matrix file supplied and creates a Pandas DataFrame, also throws exceptions if the file format is not excel (.xlsx)
    """
    global master_file_uploaded, master_matrix_dataframe

    read_cols = ["Corp", "CONCATENATE", "RESI EID", "Market", "Altice One"]
    try:
        master_matrix_dataframe = pd.read_excel(
            master_matrix_path.file,
            usecols=read_cols,
            converters={"Corp": str, "CONCATENATE": str},
        )
    except ImportError as e:
        master_file_uploaded = False
        return e
    except FileNotFoundError:
        master_file_uploaded = False
        return e
    except ValueError as e:
        master_file_uploaded = False
        if (
            "Excel file format cannot be determined, you must specify an engine manually"
            in e.args[0]
        ):
            return "Please upload an excel file only."
        elif (
            "Usecols do not match columns, columns expected but not found" in e.args[0]
        ):
            error_column_name = str(e)[str(e).index("'") :].replace("]", "")
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
        eid_dataframe = pd.read_excel(
            eid_path.file,
            usecols=["ELIGIBILITY_ID", "OFFER_ID"],
            converters={"ELIGIBILITY_ID": str, "OFFER_ID": str},
        )
    except ImportError as e:
        eid_file_uploaded = False
        return e
    except FileNotFoundError:
        eid_file_uploaded = False
        pass
    except ValueError as e:
        eid_file_uploaded = False
        if (
            "Excel file format cannot be determined, you must specify an engine manually"
            in e.args[0]
        ):
            return "Please upload an excel file only."
        elif (
            "Usecols do not match columns, columns expected but not found" in e.args[0]
        ):
            error_column_name = str(e)[str(e).index("'") :].replace("]", "")
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
        if master_matrix_dataframe["RESI EID"][i] == eid:
            a = f"""{master_matrix_dataframe['CONCATENATE'][i][:4]}-{master_matrix_dataframe['CONCATENATE'][i][4:]} - {master_matrix_dataframe['Market'][i].strip()}"""
            corp_ftax.append(a)

    if corp_ftax:
        final_eid_result_df = create_output_table(corp_ftax)
    else:
        final_eid_result_df = f"""<div class="alert alert-danger text-center" role="alert">{eid} invalid. Please try a different value.</div>"""
    return final_eid_result_df


def get_corp_ftax_from_offer_id(env: str, offer_id: str) -> None:
    """
    get_corp_ftax_from_offer_id - Displays the corp and ftax combination depending on the environment and offer ID passed. 

    Takes environment and offer ID and displays the corp and ftax combinations as well as Market type supported in that corp-ftax combination.

    :param env: Environment for which the combinations are requested. Values passed from th GUI to avoid incorrect values.
    :type env: str
    :param offer_id: Offer ID to check the corp-ftax combination.
    :type offer_id: str
    """

    if env == "QA INT":
        corp = ['7702', '7704', '7710', '7715']
    elif env == "QA 1":
        corp = ['7708', '7711']
    elif env == "QA 2":
        corp = ['7712', '7709']
    elif env == "QA 3":
        corp = ['7707', '7714']
    else:
        corp = ['7701', '7703', '7705', '7706', '7713']

    corpftax_altice_list = []
    corpftax_legacy_list = []
    smb_list = []

    offer_eid = {eid_dataframe['ELIGIBILITY_ID'][i] for i in eid_dataframe.index if eid_dataframe['OFFER_ID'][i] == offer_id}
    for j in master_matrix_dataframe.index:
        if master_matrix_dataframe['Corp'][j] in corp:
            if master_matrix_dataframe['Altice One'][j] == 'Y' and master_matrix_dataframe['RESI EID'][j] in offer_eid:
                corpftax_altice_list.append(
                    f"{master_matrix_dataframe['CONCATENATE'][j][:4]}-{master_matrix_dataframe['CONCATENATE'][j][4:]} - {master_matrix_dataframe['Market'][j].strip()} - {master_matrix_dataframe['RESI EID'][j].strip()}")

            elif master_matrix_dataframe['Altice One'][j] == 'N' and master_matrix_dataframe['RESI EID'][j] in offer_eid:
                corpftax_legacy_list.append(
                    f"{master_matrix_dataframe['CONCATENATE'][j][:4]}-{master_matrix_dataframe['CONCATENATE'][j][4:]} - {master_matrix_dataframe['Market'][j].strip()} - {master_matrix_dataframe['RESI EID'][j].strip()}")

            elif master_matrix_dataframe['RESI EID'][j] in offer_eid:
                smb_list.append(f"{master_matrix_dataframe['CONCATENATE'][j][:4]}-{master_matrix_dataframe['CONCATENATE'][j][4:]} - {master_matrix_dataframe['Market'][j].strip()} - {master_matrix_dataframe['RESI EID'][j].strip()}")


    if corpftax_legacy_list or corpftax_altice_list:
        altice_result = create_output_table(corpftax_altice_list)
        legacy_result = create_output_table(corpftax_legacy_list)
        return (altice_result, legacy_result), True

    elif smb_list:
        smb_result = create_output_table(smb_list)
        return smb_result, False
    else:
        return f"""<div class="alert alert-danger text-center" role="alert">Offer {offer_id} not present in {env}. Try a different ID.</div>""", False

def create_output_table(result):
    final_eid_result = [result[x : x + 6] for x in range(0, len(result) - 1, 6)]
    final_eid_result_df = (
        pd.DataFrame(final_eid_result)
        .to_html(
            classes=["table", "table-striped", "table-bordered"],
            index=False,
            justify="center",
            header=False,
        )
        .replace("<td>", '<td class="text-center">')
    )
    return final_eid_result_df

if __name__ == "__main__":
    uvicorn.run(app, port=8080, host='0.0.0.0')