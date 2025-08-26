import os
import boto3
import sys

import tomllib  # Use tomli for Python <3.11
from dotenv import load_dotenv

from managers.iam_role_manager import IamRoleManager
from managers.lambda_manager import LambdaManager
from managers.api_gateway.factory import ApiGatewayFactory
from util.config_loader import load_config
from util.lambda_utils import cleanup_permissions, load_lambda_functions_grouped


def main():
    # Get environment
    stage = os.getenv("STAGE", "dev")

    # Load .env variables
    load_dotenv()

    # Load TOML configuration
    with open("config.toml", "rb") as f:
        toml_data = tomllib.load(f)

    config = load_config(file_path="config.toml", stage=stage)

    region = config["stage"].get("region")
    account_id = config["stage"].get("account_id")

    # Shared clients
    iam_client = boto3.client("iam", region_name=region)
    lambda_client = boto3.client("lambda", region_name=region)

    # 1. Setup IAM Roles
    for role_key, role_cfg in config.get("iam_roles", {}).items():
        print(f"\n🔐 Setting up IAM Role: {role_key}")
        iam_manager = IamRoleManager(
            config=role_cfg,
            iam_client=iam_client,
            account_id=account_id,
            region=region,
            stage=config["stage"].get("stage_name"),
            extra_vars={
                "key_id": config["stage"].get("key_id"),
                "parameter": config["stage"].get("parameter"),
            }
        )
        iam_manager.setup_role()

    # 2. Deploy Lambda Functions
    lambda_configs = load_lambda_functions_grouped(toml_data)
    for lambda_key, lambda_cfg in lambda_configs.items():
        print(f"\n🚀 Deploying Lambda: {lambda_key} ({lambda_cfg.get('function_name')})")
        lambda_manager = LambdaManager(
            config=lambda_cfg,
            region=lambda_cfg.get("region", region),
            lambda_client=lambda_client,
            iam_client=iam_client
        )
        try:
            lambda_manager.deploy()
        except Exception as e:
            print(f"❌ Failed to deploy Lambda '{lambda_key}': {e}")

    # 3. Setup API Gateways
    for api_key, api_cfg in config.get("apis", {}).items():
        print(f"\n🌐 Setting up API Gateway: {api_key}")
        protocol_type = api_cfg.get("api_type", "REST").upper()

        # Select appropriate client
        apigateway_client = boto3.client(
            "apigatewayv2" if protocol_type == "HTTP" else "apigateway",
            region_name=region
        )

        # Clean up Lambda permissions if a Lambda integration is configured
        if api_cfg.get("integration_target") == "LAMBDA":
            lambda_fn_name = api_cfg.get("lambda_function_name")
            if lambda_fn_name:
                cleanup_permissions(lambda_client, lambda_fn_name)

        try:
            print(f"🔧 Creating API Gateway manager for: {protocol_type}")
            api_manager = ApiGatewayFactory.get_manager(
                protocol_type=protocol_type,
                api_config=api_cfg,
                stage_config=config["stage"],
                resource_methods=api_cfg.get("resources", {}) or api_cfg.get("routes", {}),
                usage_plan_config=api_cfg.get("usage_plan", {}),
                apigateway_client=apigateway_client,
                lambda_client=lambda_client
            )
            api_manager.run_setup()
        except Exception as e:
            print(f"❌ Error setting up API '{api_key}': {e}")


if __name__ == "__main__":
    main()
