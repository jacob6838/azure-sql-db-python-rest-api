import os
import pyodbc
import hashlib
import uuid

from fastapi import FastAPI, Header, HTTPException, status, Request
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

app = FastAPI(title="Work Zone Data Collection Tool Rest API")
# app = Flask(__name__)
# api = Api(app)

storage_conn_str = 'DefaultEndpointsProtocol=https;AccountName=neaeraiotstorage;AccountKey=gSFq2szM88ag0BV/J7QqzoXdak1aIGsUgyWagsR/96mlVnQhdOTnns6D7z8nOgRUdQy3FdbMxEmufrCqmE6mdw==;EndpointSuffix=core.windows.net'
sql_conn_str = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:wzdc-api-server.database.windows.net,1433;Database=wzdc-api-database;Uid=wzdc-api-user;Pwd=8QNiutu8fgBm;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
# storage_conn_str = os.environ['storage_connection_string']
# sql_conn_str = os.environ['sql_connection_string']
blob_service_client = BlobServiceClient.from_connection_string(storage_conn_str)

auth_email = "tony@neaeraconsulting.com"

# incremented primary keys
# datetime entered
# datetime updates
# isDeleted


# # --------------------------
# CREATE TABLE ApiKeys (
#     ID int NOT NULL IDENTITY(1,1),
#     ApiKeyHash varchar(64) NOT NULL UNIQUE,
#     Email varchar(320),
#     DateCreated DATETIME NOT NULL,
#     DateUpdated DATETIME,
# 	IsDeleted bit,
# );


# # --------------------------
# CREATE PROCEDURE create_key @key varchar(64)
# AS

# insert into ApiKeys (ApiKeyHash, DateCreated)
# values(@key, GETDATE())

# GO;


# # --------------------------
# CREATE PROCEDURE create_key_with_email @key varchar(64), @email varchar(254)
# AS

# insert into ApiKeys (ApiKeyHash, Email, DateCreated)
# values(@key, @email, GETDATE())

# GO;


# # --------------------------
# CREATE PROCEDURE delete_key @key varchar(64)
# AS

# delete from ApiKeys where ApiKeyHash = @key

# GO;


# # --------------------------
# CREATE PROCEDURE find_key @key varchar(64)
# AS

# select 1 from ApiKeys where ApiKeyHash = @key and (IsDeleted != 1 or IsDeleted is null)

# GO;






# validate incident data function
# check for required fields

# push invalid data to pubsub topic

cnxn = pyodbc.connect(sql_conn_str)
cursor = cnxn.cursor()

storedProcCreate = 'exec create_key @key = \'{0}\''
storedProcCreateWithEmail = "exec create_key_with_email @key = \'{0}\' @email = \'{1}\'"
storedProcDelete = "exec delete_key @key = \'{0}\'"
storedProcFind = "exec find_key @key = \'{0}\'"

authorization_key_header = 'auth_key'

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/rsm/xml/{rsm_name}") #, response_model=schemas.User
def get_rsm_file(rsm_name: str, request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_name = 'publishedworkzones'
    blob_name = 'rsm-xml/' + rsm_name

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        return {'data': blob_client.download_blob().readall().decode('utf-8')}
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail="Specified xml RSM file not found. Try /rsm/xml-list to return a list of current RSM files",
        )


@app.get("/rsm/xml-list/") #, response_model=schemas.User
def get_rsm_files_list(request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_name = 'publishedworkzones'
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with='rsm-xml/')
    blob_names = []
    for blob in blob_list:
        blob_names.append({'name': blob.name, 'etag': blob.etag})
    return {'data': blob_names}

@app.get("/rsm/uper/{rsm_name}") #, response_model=schemas.User
def get_rsm_uper_file(rsm_name, request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_name = 'publishedworkzones'
    blob_name = 'rsm-uper/' + rsm_name
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        return {'data': str(blob_client.download_blob().readall())}
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail="Specified uper RSM file not found. Try /rsm/uper-list to return a list of current RSM files",
        )

@app.get("/rsm/uper-list/") #, response_model=schemas.User
def get_rsm_uper_files_list(request: Request):
    auth_key = request.headers.get(authorization_key_header)
    valid = authenticate_key(auth_key)
    if not valid:
        get_correct_response(auth_key)
    
    container_name = 'publishedworkzones'
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(name_starts_with='rsm-uper/')
    blob_names = []
    for blob in blob_list:
        blob_names.append({'name': blob.name, 'etag': blob.etag})
    return {'data': blob_names}

# def get(self, email):
#     print(email)
#     key = create_key()

#     if key:
#         return {'auth_key': key, 'instructions': "Save this key and add it to the header of your future API calls as '{0}'".format(authorization_key_header)}
#     else:
#         return 'Failed to create credential', 500

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

# def create_key():
#     key, key_hash = generate_key()
    
#     try:
#         cursor.execute(storedProcCreate.format(key_hash))
#         cnxn.commit()
#         # for result in cursor.stored_results():
#         #     print(result.fetchall())
#     except Exception as e:
#         print(e)
#         return None

#     return key

def find_key(key_hash):
    cursor.execute(storedProcFind.format(key_hash))

    row = cursor.fetchone()

    if row:
        return True
    else:
        return False

def exec_sql(cmd):
    cursor.execute(cmd)
    row = cursor.fetchone()
    while row:
        # Print the row
        print(row)
        row = cursor.fetchone()

# api.add_resource(MANAGEMENT, '/new-user/<string:email>')

# api.add_resource(RSM_XML, '/rsm/xml/<string:rsm_name>')
# api.add_resource(RSM_XML_LIST, '/rsm/xml-list')
# api.add_resource(RSM_UPER, '/rsm/uper/<string:rsm_name>')
# api.add_resource(RSM_UPER_LIST, '/rsm/uper-list')

if __name__ == '__main__':
    app.run(debug=True)
    