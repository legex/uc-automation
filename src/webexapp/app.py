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
from ldapapi.updateldap import (
    update_contacts_num,
    update_contacts_num_withDID,
    update_general_contacts_num_withDID
    )
from webexapp.services.ldap_batch import batch_update_ldap, batch_update_ldap_acd
from webexapp.services.webex_batch import batch_update_webex_gen, batch_update_webex_acd
from webexapp.models.query_models import QueryModelLdap, QueryModelWebex, QueryModelNumberSingle, QueryModelRPSingle
from webexapp.services.rp_batch import batch_routepattern_auto
#from src.webexapp.webexbotbaseunused import WebexbotBase
from cucmapi.axlroutepattern import AXLRoutePatternOperations
from webexapi.webexgeneral import WebexGenMigration
from webexapi.webexACD import WebexMigACD
from webexapi.webexoperations import WebexOperation
from webexapi.webexnumberadd import addnumbersingle, addnumberbatch
from utils.logger import setup_logger
# Load environment variables from .env file
load_dotenv()
# API_TOKEN = os.getenv("WEBEXBOTTOKEN")
templates = Jinja2Templates(directory="webexapp/templates")
logger = setup_logger('webapp', '/a/logs/webapp.log')
axlrp = AXLRoutePatternOperations()
webex_mig_gen = WebexGenMigration()
webex_acd_mig = WebexMigACD()
webop = WebexOperation()

#webexbot = WebexbotBase()
app = FastAPI(
    title="UnifyX",
    description="Unified platform for managing CUCM and Webex user configurations, "
                "LDAP updates, license management, and route pattern operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
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
    logger.info("Homepage accessed from %s", request.client.host if request.client else "unknown")
    return templates.TemplateResponse("index_new.html", {"request": request})

@app.get("/api/ldap-services", response_class=HTMLResponse)
async def ldap_services_page(request: Request):
    """
    Render the LDAP services page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered ldap_services.html template.
    """
    return templates.TemplateResponse("ldap_services.html", {"request": request})

@app.get("/api/webex-services", response_class=HTMLResponse)
async def webex_services_page(request: Request):
    """
    Render the Webex services page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered webex_services.html template.
    """
    return templates.TemplateResponse("webex_services.html", {"request": request})

@app.get("/api/routepattern-services", response_class=HTMLResponse)
async def routepattern_services_page(request: Request):
    """
    Render the route pattern services page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered routepattern_services.html template.
    """
    return templates.TemplateResponse("routepattern_services.html", {"request": request})

@app.get("/api/number-services", response_class=HTMLResponse)
async def number_services_page(request: Request):
    """
    Render the number services page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered number_services.html template.
    """
    return templates.TemplateResponse("number_services.html", {"request": request})

@app.get("/api/single-update", response_class=HTMLResponse)
async def single_update_page(request: Request):
    """
    Render the single update page UI (legacy route).
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered single_update.html template.
    """
    return templates.TemplateResponse("single_update.html", {"request": request})

@app.get("/api/batch-update", response_class=HTMLResponse)
async def batch_update_page(request: Request):
    """
    Render the batch update page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered batch_update.html template.
    """
    return templates.TemplateResponse("batch_update.html", {"request": request})

@app.get("/api/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    """
    Render the templates download page UI.
    
    Args:
        request (Request): FastAPI request object.
    
    Returns:
        HTMLResponse: The rendered templates.html template.
    """
    return templates.TemplateResponse("templates.html", {"request": request})

@app.get("/api/download/template/{template_name}")
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
    logger.info("Template download requested: %s", template_name)
    available_templates = {
        "ldap_update": "template/ldap_update_template.csv",
        "webex_general_update": "template/webex_general_update_template.csv",
        "webex_acd_update": "template/webex_general_update_template.csv",
        "number_add": "template/number_add_template.csv",
        "cucm_route_pattern": "template/cucm_route_pattern_template.csv"
    }
    file_path = available_templates.get(template_name)
    if not file_path or not os.path.exists(file_path):
        logger.error("Template not found: %s", template_name)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Template not found.")
    logger.info("Template downloaded successfully: %s", template_name)
    return FileResponse(path=file_path,
                        filename=os.path.basename(file_path),
                        media_type='application/octet-stream')

@app.post("/api/numberadd")
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
    logger.info("Number add request received with file: %s", file.filename)
    if file.content_type != 'text/csv':
        logger.error("Invalid file type for number add: %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        logger.error("Empty file uploaded for number add: %s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        logger.debug("Processing number add for file: %s", file.filename)
        response = addnumberbatch(pd.io.common.BytesIO(contents))
        pd.DataFrame(
            [response]
            ).to_csv(f"resultfiles/numberadd_response_{file.filename}",
                     mode='a',
                     header=False,
                     index=False)
        logger.info("Number add completed successfully for file: %s", file.filename)
        return {"Status": "Success"}
    except HTTPException as e:
        logger.error("HTTPException in number add for %s: %s", file.filename, str(e))
        return {"error": str(e)}

@app.post("/api/numberaddsingle")
async def number_add_single(query: QueryModelNumberSingle):
    """
    Add phone numbers to Webex locations from a CSV file.
    
    Args:
        file (UploadFile): CSV file containing columns: Country, ContactNumber.
    
    Returns:
        dict: Status message indicating success or error.
    
    Raises:
        HTTPException: 400 if file type is invalid or file is empty.
    """
    logger.info("Single number update requested for number: %s, region=%s",
                query.number if query else "None", query.region if query else "None")
    if query is None:
        logger.error("No query provided for number add single")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    try:
        logger.debug("Processing number add for Number: %s", query.number)
        addnumbersingle(query.number, query.region)
        logger.info("Single number add completed successfully for number: %s", query.number)
        return {"Status": "Success"}
    except HTTPException as e:
        logger.error("HTTPException in number add for %s: %s", query.number, str(e))
        return {"error": str(e)}

@app.get("/api/download/result/{result_type}/{filename}")
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
    logger.info("Result file download requested: type=%s, filename=%s", result_type, filename)
    # Map result types to file prefixes
    result_prefixes = {
        "ldap": "ldap_response_",
        "webex_general": "webex_migresult_",
        "webex_acd": "acd_migresult_",
        "number_add": "numberadd_response_",
        "route_pattern": "rpupdateresult_"
    }

    if result_type not in result_prefixes:
        logger.error("Invalid result type requested: %s", result_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid result type.")

    file_path = f"resultfiles/{result_prefixes[result_type]}{filename}"
    if not os.path.exists(file_path):
        logger.error("Result file not found: %s", file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="File not found.")
    logger.info("Result file downloaded successfully: %s", file_path)
    return FileResponse(path=file_path,
                        filename=f"{result_prefixes[result_type]}{filename}",
                        media_type='application/octet-stream')

@app.post("/api/updateldap/single")
async def update_ldap_numbers(query: QueryModelLdap, acd: bool = False):
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
    logger.info("Single LDAP update requested for user: %s, acd=%s",
                query.username if query else "None", acd)
    if query is None:
        logger.error("No query provided for LDAP update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    extension = query.extension
    if acd:
        try:
            update_contacts_num_withDID(
                query.username,
                internal_extension=extension,
                external_number=query.externalnumber
                )
            logger.info("LDAP update with DID completed for ACD user: %s, %s",
                        query.username, query.externalnumber)
            return {"Status": "LDAP update initiated"}
        except Exception as e:
            logger.error("Error updating LDAP with DID for ACD user %s: %s",
                            query.username, str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error updating LDAP with DID: {str(e)}") from e
    if query.externalnumber:
        externalnumber = query.externalnumber
        logger.debug("LDAP update with external number for user: %s", query.username)
        try:
            update_general_contacts_num_withDID(
                query.username,
                external_number=externalnumber,
                internal_extension=extension
                )
            logger.info("LDAP update with DID completed for general user: %s", query.username)
            return {"Status": "LDAP update initiated"}
        except Exception as e:
            logger.error("Error updating LDAP for general user %s: %s", query.username, str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error updating LDAP: {str(e)}") from e
    try:
        update_contacts_num(query.username, internal_extension=extension)
        logger.info("LDAP update completed for user: %s", query.username)
        return {"Status": "LDAP update initiated"}
    except Exception as e:
        logger.error("Error updating LDAP for user %s: %s", query.username, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error updating LDAP: {str(e)}") from e

@app.post("/api/updateldap/batch")
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
    logger.info("Batch LDAP update requested with file: %s, acd=%s",
                file.filename if file else "None", acd)
    if file is None:
        logger.error("No file provided for batch LDAP update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")
    if file.content_type != 'text/csv':
        logger.error("Invalid file type for batch LDAP update: %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        logger.error("Empty file uploaded for batch LDAP update: %s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    if acd:
        try:
            logger.debug("Processing batch ACD LDAP update for file: %s", file.filename)
            response = batch_update_ldap_acd(pd.io.common.BytesIO(contents), file.filename)
            logger.info("Batch ACD LDAP update completed for file: %s", file.filename)
            return {"Status": "Success", "Detail": response}
        except HTTPException as e:
            logger.error("HTTPException in batch ACD LDAP update for %s: %s", file.filename, str(e))
            return {"error": str(e)}
        except Exception as e:
            logger.error("Error processing batch ACD LDAP file %s: %s", file.filename, str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error processing file: {str(e)}") from e
    try:
        logger.debug("Processing batch LDAP update for file: %s", file.filename)
        response = batch_update_ldap(pd.io.common.BytesIO(contents), file.filename)
        logger.info("Batch LDAP update completed for file: %s", file.filename)
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        logger.error("HTTPException in batch LDAP update for %s: %s", file.filename, str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Error processing batch LDAP file %s: %s", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e

@app.post("/api/updatewebexgeneral/single")
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
    logger.info("Single Webex general update requested for user: %s",
                query.username if query else "None")
    if query is None:
        logger.error("No query provided for Webex update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    if query.externalnumber:
        logger.debug("Webex update with external number for user: %s", query.username)
        try:
            webex_results = webex_acd_mig.patch_dn_acd(
                query.username,
                query.externalnumber,
                query.extension,
                query.region
                )
            logger.info("Webex update with DID completed for user: %s", query.username)
            return {"Status": "Webex update initiated", "Detail": webex_results}
        except Exception as e:
            logger.error("Error updating Webex with DID for user %s: %s", query.username, str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Error updating Webex with DID: {str(e)}") from e
    try:
        webex_results = webex_mig_gen.patch_license_dn(
            query.username,
            query.extension,
            query.region
            )
        logger.info("Webex update completed for user: %s", query.username)
        return {"Status": "Webex update initiated", "Detail": webex_results}
    except Exception as e:
        logger.error("Error updating Webex for user %s: %s", query.username, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error updating Webex: {str(e)}") from e

@app.post("/api/updatewebexgeneral/batch")
async def batch_update_webex_general(start_extension: str = None,file: UploadFile | None = None):
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
    logger.info("Batch Webex general update requested with file: %s",
                file.filename if file else "None")
    if file is None:
        logger.error("No file provided for batch Webex update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")
    if start_extension is None:
        logger.error("No start_extension provided for batch Webex update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="start_extension must be provided.")
    if file.content_type != 'text/csv':
        logger.error("Invalid file type for batch Webex update: %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        logger.error("Empty file uploaded for batch Webex update: %s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        logger.debug("Processing batch Webex general update for file: %s", file.filename)
        response = batch_update_webex_gen(pd.io.common.BytesIO(contents),
                                          file.filename,
                                          start_extension
                                          )
        logger.info("Batch Webex general update completed for file: %s", file.filename)
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        logger.error("HTTPException in batch Webex update for %s: %s", file.filename, str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Error processing batch Webex file %s: %s", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e

@app.post("/api/updatewebexacd/single")
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
    logger.info("Single Webex ACD update requested for user: %s",
                query.username if query else "None")
    if query is None:
        logger.error("No query provided for Webex ACD update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    if query:
        if query.externalnumber:
            logger.debug("Processing Webex ACD update for user: %s", query.username)
            try:
                webex_results = webex_acd_mig.patch_dn_acd(
                    query.username,
                    query.externalnumber,
                    query.extension,
                    query.region
                    )
                logger.info("Webex ACD update completed for user: %s", query.username)
                return {"Status": "Webex ACD update initiated", "Detail": webex_results}
            except Exception as e:
                logger.error("Error updating Webex ACD for user %s: %s", query.username, str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Error updating Webex ACD with DID: {str(e)}") from e
        else:
            logger.error("External number not provided for ACD update for user: %s", query.username)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="External number must be provided for ACD updates.")

@app.post("/api/updatewebexacd/batch")
async def b_update_webex_acd(start_extension: str = None, file: UploadFile | None = None):
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
    logger.info("Batch Webex ACD update requested with file: %s", file.filename if file else "None")
    if file is None:
        logger.error("No file provided for batch Webex ACD update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File must be provided.")
    if start_extension is None:
        logger.error("No start_extension provided for batch Webex ACD update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="start_extension must be provided.")
    if file.content_type != 'text/csv':
        logger.error("Invalid file type for batch Webex ACD update: %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        logger.error("Empty file uploaded for batch Webex ACD update: %s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        logger.debug("Processing batch Webex ACD update for file: %s", file.filename)
        response = batch_update_webex_acd(pd.io.common.BytesIO(contents), file.filename, start_extension)
        logger.info("Batch Webex ACD update completed for file: %s", file.filename)
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        logger.error("HTTPException in batch Webex ACD update for %s: %s", file.filename, str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Error processing batch Webex ACD file %s: %s", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e

@app.post("/api/routepattern")
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
    logger.info("Route pattern creation requested with file: %s", file.filename)
    if file.content_type != 'text/csv':
        logger.error("Invalid file type for route pattern creation: %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Please upload a CSV file.")
    contents = await file.read()
    if not contents:
        logger.error("Empty file uploaded for route pattern creation: %s", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded file is empty")
    try:
        logger.debug("Processing route pattern creation for file: %s", file.filename)
        response = batch_routepattern_auto(
            pd.io.common.BytesIO(contents),
            file.filename
            )
        logger.info("Route pattern creation completed for file: %s", file.filename)
        return {"Status": "Success", "Detail": response}
    except HTTPException as e:
        logger.error("HTTPException in route pattern creation for %s: %s", file.filename, str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Error processing route pattern file %s: %s", file.filename, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error processing file: {str(e)}") from e

@app.post("/api/removewebexlicense/single")
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
    logger.info("Webex license removal requested for email: %s", email)
    if not email:
        logger.error("No email provided for license removal")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email must be provided.")
    try:
        logger.debug("Processing Webex license removal for: %s", email)
        result = webop.remove_webex_license(email)
        logger.info("Webex license removal completed for: %s", email)
        return {"Status": "Webex license removal initiated", "Detail": result}
    except Exception as e:
        logger.error("Error removing Webex license for %s: %s", email, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error removing Webex license: {str(e)}") from e

@app.post("/api/updateroutepattern/single")
async def update_route_pattern_single(query: QueryModelRPSingle):
    """
    Update a single route pattern in CUCM.
    
    Args:
        query (QueryModelRPSingle): Information containing route pattern and username.
    
    Returns:
        dict: Status and detail message with route pattern update result.
    """
    logger.info("Single route pattern update requested for user: %s",
                query.username if query else "None")
    if query is None:
        logger.error("No query provided for route pattern update")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query must be provided.")
    routepattern = f"\+{query.routepattern}"
    try:
        logger.debug("Processing route pattern update for user: %s", query.username)
        result = axlrp.create_routepattern(routepattern, query.username)
        logger.info("Route pattern update completed for user: %s", query.username)
        return {"Status": "Route pattern update initiated", "Detail": result}
    except Exception as e:
        logger.error("Error updating route pattern for user %s: %s", query.username, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error updating route pattern: {str(e)}") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
