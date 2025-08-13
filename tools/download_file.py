import io
import os
from collections.abc import Generator
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class DownloadFileTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Ensure runtime and credentials
        if not self.runtime or not self.runtime.credentials:
            raise Exception("Tool runtime or credentials are missing")

        # Get account name
        account_name = self.runtime.credentials.get("account_name")
        if not account_name:
            raise ValueError("Azure Blob Storage account name is required")

        # Get API key
        api_key = self.runtime.credentials.get("api_key")
        if not api_key:
            raise ValueError("Azure Blob Storage API Key is required")

        # get container name
        container_name = tool_parameters.get("container_name")
        if not container_name:
            raise ValueError("Container name is required")

        # get blob name (file name in the blob storage)
        blob_name = tool_parameters.get("blob_name")
        if not blob_name:
            raise ValueError("Blob name is required")

        # get optional local file path
        local_file_path = tool_parameters.get("local_file_path")

        # create a blob client using the connection string
        blob_service_client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net", credential=api_key
        )

        # get blob client
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        try:
            # check if blob exists
            if not blob_client.exists():
                raise ResourceNotFoundError(f"Blob '{blob_name}' not found in container '{container_name}'")

            # download blob
            download_stream = blob_client.download_blob()
            
            # if local file path is provided, save to file
            if local_file_path:
                # create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                with open(local_file_path, "wb") as local_file:
                    local_file.write(download_stream.readall())
                
                # get blob properties for response
                blob_properties = blob_client.get_blob_properties()
                result = {
                    "name": blob_properties.name,
                    "container": blob_properties.container,
                    "size": blob_properties.size,
                    "creation_time": blob_properties.creation_time.isoformat() if blob_properties.creation_time else None,
                    "last_modified": blob_properties.last_modified.isoformat() if blob_properties.last_modified else None,
                    "content_type": blob_properties.content_settings.content_type if blob_properties.content_settings else None,
                    "local_file_path": local_file_path
                }

                yield self.create_text_message(
                    f'File "{blob_name}" downloaded successfully from container "{container_name}" to "{local_file_path}".'
                )
                yield self.create_json_message(result)
                
            else:
                # return file content as binary data
                file_content = download_stream.readall()
                
                # get blob properties for response
                blob_properties = blob_client.get_blob_properties()
                result = {
                    "name": blob_properties.name,
                    "container": blob_properties.container,
                    "size": blob_properties.size,
                    "creation_time": blob_properties.creation_time.isoformat() if blob_properties.creation_time else None,
                    "last_modified": blob_properties.last_modified.isoformat() if blob_properties.last_modified else None,
                    "content_type": blob_properties.content_settings.content_type if blob_properties.content_settings else None,
                    "content_size_bytes": len(file_content)
                }

                yield self.create_text_message(
                    f'File "{blob_name}" downloaded successfully from container "{container_name}".'
                )
                yield self.create_json_message(result)
                yield self.create_blob_message(blob=file_content, meta=result)

        except ResourceNotFoundError as e:
            raise Exception(f"File not found: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}") from e
