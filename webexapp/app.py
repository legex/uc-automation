"""FastAPI Web Application for CUCM and Webex Management.

This is the main web application module providing REST API endpoints and
web UI for managing CUCM (Cisco Unified Communications Manager) and Webex
user configurations, including:

- LDAP contact number updates
- Webex license and extension management
- Route pattern creation in CUCM
- Batch operations via CSV file uploads
- Template downloads for bulk operations

Environment Variables Required:
    WEBEXBOTTOKEN: Webex bot token for API authentication
    (Other tokens loaded from .env via submodules)
"""
import os
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, HTTPException, status, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ldapapi.updateldap import update_contacts_num, update_contacts_num_withDID, update_general_contacts_num_withDID
from webexapp.services.ldap_batch import batch_update_ldap, batch_update_ldap_acd
from webexapp.services.webex_batch import batch_update_webex_gen, batch_update_webex_acd
from webexapp.models.query_models import QueryModelLdap, QueryModelWebex
from webexapp.services.rp_batch import batch_routepattern_auto
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from webexapi.webexnumberadd import addnumber
from webexapp.webexbotbase import WebexbotBase
from utils.logger import setup_logger
# Load environment variables from .env file
load_dotenv()
API_TOKEN = os.getenv("WEBEXBOTTOKEN")
templates = Jinja2Templates(directory="webexapp/templates")
logger = setup_logger('webapp', 'log/webapp.log')
axlrp = AXLRoutePatternOperations()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
webop = WebexOperation()

webexbot = WebexbotBase()
app = FastAPI()
# orgId = ""
# @app.post("/roomwebhook")
# async def room_webhook(request: Request):
#     payload = await request.json()
#     if payload.get("orgId") != orgId:
#         return {"status": "ignored"}
#     data = payload.get("data", {})
#     room_id = data.get("id")
#     if room_id:
#         webexbot.send_message(room_id, "Hello! Welcome to the Webex Room.")
#     return {"status": "success"}


@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    """
    Render the main homepage UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered index_new.html template.
    """
    return templates.TemplateResponse("index_new.html", {"request": request})

@app.get("/single-update", response_class=HTMLResponse)
async def single_update_page(request: Request):
    """
    Render the single update page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered single_update.html template.
    """
    return templates.TemplateResponse("single_update.html", {"request": request})

@app.get("/batch-update", response_class=HTMLResponse)
async def batch_update_page(request: Request):
    """
    Render the batch update page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered batch_update.html template.
    """
    return templates.TemplateResponse("batch_update.html", {"request": request})

@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    """
    Render the templates download page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered templates.html template.
    """
    return templates.TemplateResponse("templates.html", {"request": request})

@app.get("/download/template/{template_name}")
async def download_template(template_name: str):
    """
    Download a CSV template file for batch operations.
    
    Args:
        template_name (str): Name of the template to download. Available options:
            - ldap_update
            - webex_general_update
            - webex_acd_update
            - number_add
            - cucm_route_pattern
    
    Returns:
        FileResponse: The requested CSV template file.
    
    Raises:
        HTTPException: 404 if template not found.
    """
    available_templates = {
        "ldap_update": "template/ldap_update_template.csv",
        "webex_general_update": "template/webex_general_update_template.csv",
        "webex_acd_update": "template/webex_general_update_template.csv",
        "number_add": "template/number_add_template.csv",
        "cucm_route_pattern": "template/cucm_route_pattern_template.csv"
    }
    file_path = available_templates.get(template_name)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Template not found.")
    return FileResponse(path=file_path,
                        filename=os.path.basename(file_path),
                        media_type='application/octet-stream')

@app.post("/numberadd")
async def number_add(file: UploadFile):
    """
    Add phone numbers to Webex locations from a CSV file.
    
    Args:
        file (UploadFile): CSV file containing columns: Country, ContactNumber.
    
    Returns:
        dict: Status message indicating success or error.
    
    Raises:
        HTTPException: 400 if file type is invalid or file is empty.
    """
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

@app.get("/download/result/{result_type}/{filename}")
async def download_result_file(result_type: str, filename: str):
    """
    Download a result file from a previous batch operation.
    
    Args:
        result_type (str): Type of result file. Options: ldap, webex_general,
                          webex_acd, number_add, route_pattern.
        filename (str): Name of the original uploaded file.
    
    Returns:
        FileResponse: The result CSV file.
    
    Raises:
        HTTPException: 400 if result_type is invalid, 404 if file not found.
    """
    # Map result types to file prefixes
    result_prefixes = {
        "ldap": "ldap_response_",
        "webex_general": "webex_migresult_",
        "webex_acd": "acd_migresult_",
        "number_add": "numberadd_response_",
        "route_pattern": "rpupdateresult_"
    }

    if result_type not in result_prefixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid result type.")

    file_path = f"resultfiles/{result_prefixes[result_type]}{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="File not found.")
    return FileResponse(path=file_path,
                        filename=f"{result_prefixes[result_type]}{filename}",
                        media_type='application/octet-stream')

@app.post("/updateldap/single")
async def update_ldap_numbers(query: QueryModelLdap, acd: bool = Form(False)):
    """
    Update LDAP contact numbers for a single user.
    
    Args:
        query (QueryModelLdap): User information containing username, extension,
                               and optional external number.
        acd (bool): If True, update as ACD contact; otherwise general contact.
    
    Returns:
        dict: Status message indicating LDAP update initiated.
    
    Raises:
        HTTPException: 400 if query is invalid, 500 if LDAP update fails.
    """
    if query is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    extension = query.extension
    if query.externalnumber:
        externalnumber = query.externalnumber
        if acd:
            try:
                update_contacts_num_withDID(
                    query.username,
                    internal_extension=extension,
                    external_number=externalnumber
                    )
                return {"Status": "LDAP update initiated"}
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error updating LDAP with DID: {str(e)}") from e
        try:
            update_general_contacts_num_withDID(
                query.username,
                external_number=externalnumber,
                internal_extension=extension
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

@app.post("/updateldap/batch")
async def batch_update_ldap_numbers(file: UploadFile, acd: bool = Form(False)):
    """
    Batch update LDAP contact numbers from a CSV file.
    
    Args:
        file (UploadFile): CSV file containing columns: UserId, targetNum,
                          and optional ExternalNumber.
        acd (bool): If True, process as ACD contacts; otherwise general contacts.
    
    Returns:
        dict: Status and detail message indicating completion.
    
    Raises:
        HTTPException: 400 if file is invalid or empty, 500 if processing fails.
    """
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    if acd:
        try:
            response = batch_update_ldap_acd(pd.io.common.BytesIO(contents), file.filename)
            return {"Status": "Success", "Detail": response}
        except HTTPException as e:
            return {"error": str(e)}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error processing file: {str(e)}") from e
    try:
        response = batch_update_ldap(pd.io.common.BytesIO(contents), file.filename)
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        return {"error": str(e)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e

@app.post("/updatewebexgeneral/single")
async def update_webex_general(query: QueryModelWebex):
    """
    Update Webex settings for a single user.
    
    Args:
        query (QueryModelWebex): User information containing username, extension,
                                region, and optional external number.
    
    Returns:
        dict: Status and detail message with Webex update results.
    
    Raises:
        HTTPException: 400 if query is invalid, 500 if Webex update fails.
    """
    if query is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
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

@app.post("/updatewebexgeneral/batch")
async def batch_update_webex_general(file: UploadFile | None = None):
    """
    Batch update Webex settings from a CSV file.
    
    Args:
        file (UploadFile | None): CSV file containing columns: UserId, Email,
                                  extension, Country, and optional ContactNumber.
    
    Returns:
        dict: Status and detail message indicating completion.
    
    Raises:
        HTTPException: 400 if file is invalid or empty, 500 if processing fails.
    """
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")
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

@app.post("/updatewebexacd/single")
async def update_webex_acd(query: QueryModelWebex):
    """
    Update Webex ACD (Automatic Call Distribution) settings for a single user.
    
    Args:
        query (QueryModelWebex): User information containing username, extension,
                                region, and external number (required for ACD).
    
    Returns:
        dict: Status and detail message with Webex ACD update results.
    
    Raises:
        HTTPException: 400 if query is invalid or external number missing,
                      500 if Webex ACD update fails.
    """
    if query is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
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

@app.post("/updatewebexacd/batch")
async def b_update_webex_acd(file: UploadFile | None = None):
    """
    Batch update Webex ACD settings from an Excel file.
    
    Args:
        file (UploadFile | None): Excel file containing columns: UserId, Email,
                                 extension, Country, and ContactNumber.
    
    Returns:
        dict: Status and detail message indicating completion.
    
    Raises:
        HTTPException: 400 if file is invalid or empty, 500 if processing fails.
    """
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")

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
    """
    Create route patterns in CUCM from a CSV file.
    
    Args:
        file (UploadFile): CSV file containing columns: ContactNumber and UserId.
    
    Returns:
        dict: Status and detail message indicating completion.
    
    Raises:
        HTTPException: 400 if file type is invalid or file is empty,
                      500 if route pattern creation fails.
    """
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

@app.post("/removewebexlicense/single")
async def remove_webex_license(email: str = Form(...)):
    """
    Remove Webex license from a single user.
    
    Args:
        email (str): Email address of the user whose Webex license should be removed.
    
    Returns:
        dict: Status and detail message with license removal result.
    
    Raises:
        HTTPException: 400 if email is not provided, 500 if license removal fails.
    """
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email must be provided.")
    try:
        result = webop.remove_webex_license(email)
        return {"Status": "Webex license removal initiated", "Detail": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error removing Webex license: {str(e)}") from e
