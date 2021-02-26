from flask import Flask, request
from azure.storage.blob import BlobServiceClient
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

conn_str = 'DefaultEndpointsProtocol=https;AccountName=neaeraiotstorage;AccountKey=gSFq2szM88ag0BV/J7QqzoXdak1aIGsUgyWagsR/96mlVnQhdOTnns6D7z8nOgRUdQy3FdbMxEmufrCqmE6mdw==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(conn_str)

class RSM_XML(Resource):
    def get(self, rsm_name):
        container_name = 'publishedworkzones'
        blob_name = 'rsm-xml/' + rsm_name
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        return {'data': blob_client.download_blob().readall().decode('utf-8')}

class RSM_XML_LIST(Resource):
    def get(self):
        container_name = 'publishedworkzones'
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs(name_starts_with='rsm-xml/')
        blob_names = []
        for blob in blob_list:
            blob_names.append({'name': blob.name, 'etag': blob.etag})
        return {'data': blob_names}

class RSM_UPER(Resource):
    def get(self, rsm_name):
        container_name = 'publishedworkzones'
        blob_name = 'rsm-uper/' + rsm_name
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        return {'data': str(blob_client.download_blob().readall())}

class RSM_UPER_LIST(Resource):
    def get(self):
        container_name = 'publishedworkzones'
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs(name_starts_with='rsm-uper/')
        blob_names = []
        for blob in blob_list:
            blob_names.append({'name': blob.name, 'etag': blob.etag})
        return {'data': blob_names}

api.add_resource(RSM_XML, '/rsm/xml/<string:rsm_name>')
api.add_resource(RSM_XML_LIST, '/rsm/xml-list')
api.add_resource(RSM_UPER, '/rsm/uper/<string:rsm_name>')
api.add_resource(RSM_UPER_LIST, '/rsm/uper-list')

# if __name__ == '__main__':
#     app.run() #debug=True