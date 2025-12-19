import json
import os
import pandas as pd
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from ldapapi.updateldap import update_contacts_num, update_contacts_num_withDID
from webexapp.main import batch_routepattern_auto, batch_update_ldap, batch_update_webex_gen, batch_update_webex_acd
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from webexapi.webexnumberadd import addnumber
from webexapp.webexbotbase import WebexbotBase
from utils.logger import setup_logger
# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv("WEBEXBOTTOKEN")

logger = setup_logger('webapp', 'log/webapp.log')
prefixes = extension_prefix
axloperations = AXLOperations()
axlrp = AXLRoutePatternOperations()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
currentdir = os.getcwd()
webop = WebexOperation()

class QueryModelLdap(BaseModel):
    username: str
    extension: str
    externalnumber: str | None = None

class QueryModelWebex(BaseModel):
    username: str
    extension: str
    region: str
    externalnumber: str | None = None


webexbot = WebexbotBase()
app = FastAPI()
orgId = ""
@app.post("/roomwebhook")
async def room_webhook(request: Request):
    payload = await request.json()
    if payload.get("orgId") != orgId:
        return {"status": "ignored"}
    data = payload.get("data", {})
    room_id = data.get("id")
    if room_id:
        webexbot.send_message(room_id, "Hello! Welcome to the Webex Room.")
    return {"status": "success"}


@app.get("/download/template/{template_name}")
async def download_template(template_name: str):
    templates = {
        "ldap_update": "templates/ldap_update_template.csv",
        "webex_general_update": "templates/webex_general_update_template.csv",
        "webex_acd_update": "templates/webex_acd_update_template.csv",
        "number_add": "templates/number_add_template.csv",
        "cucm_route_pattern": "templates/cucm_route_pattern_template.csv"
    }
    file_path = templates.get(template_name)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Template not found.")
    return FileResponse(path=file_path,
                        filename=os.path.basename(file_path),
                        media_type='application/octet-stream')

@app.post("/numberadd")
async def number_add(file: UploadFile):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        response = addnumber(pd.io.common.BytesIO(contents))
        pd.DataFrame(
            [response]
            ).to_csv(f"resultfiles/numberadd_response_{file.filename}",
                     mode='a',
                     header=False,
                     index=False)
        return {"Status": "Success"}
    except HTTPException as e:
        return {"error": str(e)}

@app.get("/download/{filename}")
async def download_numberadd_response(filename: str):
    file_path = f"resultfiles/numberadd_response_{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="File not found.")
    return FileResponse(path=file_path,
                        filename=f"numberadd_response_{filename}",
                        media_type='application/octet-stream')

@app.post("/updateldap")
async def update_ldap_numbers(query: QueryModelLdap | None = None,
                              file: UploadFile | None = None):
    if query is None and file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Either query or file must be provided.")
    if query:
        extension = query.extension
        if query.externalnumber:
            externalnumber = query.externalnumber
            try:
                update_contacts_num_withDID(
                    query.username,
                    internal_extension=extension,
                    external_number=externalnumber
                    )
                return {"Status": "LDAP update initiated"}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error updating LDAP: {str(e)}") from e
        try:
            update_contacts_num(query.username, internal_extension=extension)
            return {"Status": "LDAP update initiated"}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error updating LDAP: {str(e)}") from e
    if file:
        if file.content_type != 'text/csv':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file type. Please upload a CSV file.")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Uploaded file is empty")
        try:
            response = batch_update_ldap(pd.io.common.BytesIO(contents), file.filename)
            return {"Status": "Success", "Detail": response}
        except HTTPException as e:
            return {"error": str(e)}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error processing file: {str(e)}") from e

@app.post("/updatewebexgeneral")
async def update_webex_general(query: QueryModelWebex | None = None,
                                 file: UploadFile | None = None):
    if query is None and file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Either query or file must be provided.")
    if query:
        if query.externalnumber:
            try:
                webex_results = webex_acd_mig.patch_dn_acd(
                    query.username,
                    query.externalnumber,
                    query.extension,
                    query.region
                    )
                return {"Status": "Webex update initiated", "Detail": webex_results}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error updating Webex with DID: {str(e)}") from e
        try:
            webex_results = webex_mig_gen.patch_license_dn(
                query.username,
                query.extension,
                query.region
                )
            return {"Status": "Webex update initiated", "Detail": webex_results}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error updating Webex: {str(e)}") from e
    if file:
        if file.content_type != 'text/csv':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file type. Please upload a CSV file.")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Uploaded file is empty")
        try:
            response = batch_update_webex_gen(pd.io.common.BytesIO(contents), file.filename)
            return {"Status": "Success", "Detail": response}
        except HTTPException as e:
            return {"error": str(e)}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error processing file: {str(e)}") from e

@app.post("/updatewebexacd")
async def update_webex_acd(query: QueryModelWebex | None = None,
                                 file: UploadFile | None = None):
    if query is None and file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Either query or file must be provided.")
    if query:
        if query.externalnumber:
            try:
                webex_results = webex_acd_mig.patch_dn_acd(
                    query.username,
                    query.externalnumber,
                    query.extension,
                    query.region
                    )
                return {"Status": "Webex ACD update initiated", "Detail": webex_results}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error updating Webex ACD with DID: {str(e)}") from e
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="External number must be provided for ACD updates.")
    if file:
        if file.content_type != 'text/csv':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file type. Please upload a CSV file.")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Uploaded file is empty")
        try:
            response = batch_update_webex_acd(pd.io.common.BytesIO(contents), file.filename)
            return {"Status": "Success", "Detail": response}
        except HTTPException as e:
            return {"error": str(e)}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error processing file: {str(e)}") from e

@app.post("/routepattern")
async def create_route_pattern(file: UploadFile):
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        response = batch_routepattern_auto(
            pd.io.common.BytesIO(contents),
            file.filename
            )
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        return {"error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e
