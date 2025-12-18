import json
import os
import pandas as pd
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from ldapapi.updateldap import update_contacts_num, update_contacts_num_withDID
from webexapp.main import batch_update_ldap
from cucmapi.axlop import AXLOperations
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from metadata.settings import extension_prefix
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from webexapi.webexnumberadd import addnumber
from webexapp.webexbotbase import WebexbotBase
from utils.logger import setup_logger
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

@app.get("/download/numberadd/{filename}")
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
