from typing import Any

from azure.storage.blob import BlobServiceClient
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class AzureBlobStorageProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            account_name = credentials.get("account_name")
            api_key = credentials.get("api_key")

            # ensure account name and api key are provided
            if not account_name:
                raise Exception("Azure Blob Storage Account Name is required")
            if not api_key:
                raise Exception("Azure Blob Storage API Key is required")

            # validate connection string
            try:
                blob_service_client = BlobServiceClient(
                    account_url=f"https://{account_name}.blob.core.windows.net", credential=api_key
                )
                containers = blob_service_client.list_containers()
                containers_count = len(list(containers))  # noqa: F841
            except Exception as e:
                raise Exception("Invalid Azure Blob Storage connection string") from e

        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e)) from e
