import re
from typing import Dict, Any
from botocore.client import BaseClient


def cleanup_permissions(lambda_client: BaseClient, lambda_function_name: str):
    """
    Remove existing Lambda permissions to avoid duplicate conflicts before re-adding them.
    """
    try:
        policy = lambda_client.get_policy(FunctionName=lambda_function_name)
        statements = policy.get("Policy", "")
        statement_ids = re.findall(r'"Sid"\s*:\s*"([^"]+)"', statements)

        for sid in statement_ids:
            try:
                lambda_client.remove_permission(
                    FunctionName=lambda_function_name,
                    StatementId=sid
                )
                print(f"[CLEANUP] Removed permission: {sid}")
            except Exception as e:
                print(f"[CLEANUP WARNING] Could not remove permission {sid}: {e}")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"[CLEANUP] No existing policy found for {lambda_function_name}")
    except Exception as e:
        print(f"[CLEANUP ERROR] Failed to cleanup permissions: {e}")


def load_lambda_functions_grouped(toml_data: dict) -> dict:
    functions = {}

    lambda_section = toml_data.get("lambda", {})
    for group_key, group_val in lambda_section.items():
        if not isinstance(group_val, dict):
            continue
        # Get the 'service' sub-dict if it exists
        service_config = group_val.get("service")
        if service_config:
            functions[group_key] = service_config

    return functions
