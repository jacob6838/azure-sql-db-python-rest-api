import os
import pyodbc
import hashlib
import uuid

from fastapi import FastAPI, Header, HTTPException, status, Request
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

auth_email = os.environ['auth_contact_email']

tags_metadata = [
    {
        "name": "xml-list",
        "description": "Get list of current RSM xml files, with etags (unique identifiers that change " + 
            "when a file is updated, you can save them and determine if you need to re-download updated files",
    },
    {
        "name": "xml-file",
        "description": "Download an individual RSM xml file by name (including extension)",
    },
    {
        "name": "uper-list",
        "description": "Get list of current RSM uper (binary) files, with etags (unique identifiers " + 
            "that change when a file is updated, you can save them and determine if you need to re-download updated files",
    },
    {
        "name": "uper-file",
        "description": "Download an individual RSM uper file by name (including extension)",
    },
]

app = FastAPI(
    title="Work Zone Data Collection Tool Rest API", 
    description="This API hosts work zone data collected by the WZDC " + 
        "(work zone data collection) tool. This data includes RSM messages, both in xml and uper (binary) formats. This API " + 
        f"requires an APi key in the header. Contact {auth_email} for more information on how to acquire and use an API key.",
    docs_url="/",
    openapi_tags=tags_metadata)

storage_conn_str = os.environ['storage_connection_string']
sql_conn_str = os.environ['sql_connection_string']
blob_service_client = BlobServiceClient.from_connection_string(storage_conn_str)

cnxn = pyodbc.connect(sql_conn_str)
cursor = cnxn.cursor()

storedProcFind = os.environ['stored_procedure_find_key']

authorization_key_header = 'auth_key'

container_name = os.environ['source_container_name']

@app.get("/rsm/xml-list/", tags=["xml-list"])
def get_rsm_files_list(request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with='rsm-xml/')
    blob_names = []
    for blob in blob_list:
        blob_names.append({'name': blob.name, 'etag': blob.etag})
    return {'data': blob_names}

@app.get("/rsm/xml/{rsm_name}", tags=["xml-file"])
def get_rsm_file(rsm_name: str, request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    blob_name = 'rsm-xml/' + rsm_name

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        return {'data': blob_client.download_blob().readall().decode('utf-8')}
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail="Specified xml RSM file not found. Try /rsm/xml-list to return a list of current RSM files",
        )

@app.get("/rsm/uper-list/", tags=["uper-list"])
def get_rsm_uper_files_list(request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with='rsm-uper/')
    blob_names = []
    for blob in blob_list:
        blob_names.append({'name': blob.name, 'etag': blob.etag})
    return {'data': blob_names}

@app.get("/rsm/uper/{rsm_name}", tags=["uper-file"])
def get_rsm_uper_file(rsm_name, request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    blob_name = 'rsm-uper/' + rsm_name
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        return {'data': str(blob_client.download_blob().readall())}
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail="Specified uper RSM file not found. Try /rsm/uper-list to return a list of current RSM files",
        )

def authenticate_key(key):
    try:
        key_hash = str(hashlib.sha256(key.encode()).hexdigest())
        print(key_hash)
        return find_key(key_hash)
    except:
        return False

def get_correct_response(auth_key):
    if not auth_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication key was specified. If you have a key, please add auth_key: **authentication_key** to your " + 
            f"request header. If you do not have a key, email {auth_email} to get a key.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication key",
        )

# def generate_key():
#     key = str(uuid.uuid4())
#     key_hash = str(hashlib.sha256(key.encode()).hexdigest())
#     print(key_hash)
#     return key, key_hash

def find_key(key_hash):
    cursor.execute(storedProcFind.format(key_hash))

    row = cursor.fetchone()

    if row:
        return True
    else:
        return False