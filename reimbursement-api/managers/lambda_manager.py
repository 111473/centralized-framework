import os
import json
import time

from pathlib import Path
from botocore.exceptions import ClientError


class LambdaManager:
    def __init__(self, config, region, lambda_client, iam_client):
        self.config = config
        self.region = region
        self.lambda_client = lambda_client
        self.iam_client = iam_client

    def deploy(self):
        function_name = self.config["function_name"]
        role_name = self.config["role_name"]
        runtime = self.config["runtime"]
        handler = self.config["handler"]
        zip_file_path = self.config["zip_file"]

        # Load zipped Lambda code
        if not Path(zip_file_path).exists():
            raise FileNotFoundError(f"Lambda zip file not found: {zip_file_path}")

        with open(zip_file_path, "rb") as f:
            zip_bytes = f.read()

        # Construct the IAM role ARN
        account_id = os.getenv("ACCOUNT_ID")
        if not account_id:
            raise EnvironmentError("ACCOUNT_ID environment variable not set")

        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

        # Ensure trust policy is set correctly
        self._ensure_lambda_trust_policy(role_name)

        # Check if Lambda already exists
        try:
            self.lambda_client.get_function(FunctionName=function_name)
            print(f"[INFO] Updating existing Lambda function: {function_name}")
            self._update_lambda(function_name, zip_bytes)
        except self.lambda_client.exceptions.ResourceNotFoundException:
            print(f"[INFO] Creating new Lambda function: {function_name}")
            self._create_lambda(function_name, zip_bytes, role_arn, runtime, handler)

    def _create_lambda(self, function_name, zip_bytes, role_arn, runtime, handler):
        try:
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime=runtime,
                Role=role_arn,
                Handler=handler,
                Code={"ZipFile": zip_bytes},
                Timeout=30,
                MemorySize=128,
                Publish=True
            )
            print(f"[SUCCESS] Created Lambda function: {function_name}")
        except ClientError as e:
            print(f"[ERROR] Failed to create Lambda function '{function_name}': {e}")
            raise

    def _update_lambda(self, function_name, zip_bytes):
        try:
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes,
                Publish=True
            )
            print(f"[SUCCESS] Updated Lambda code: {function_name}")
        except ClientError as e:
            print(f"[ERROR] Failed to update Lambda code for '{function_name}': {e}")
            raise

    def _ensure_lambda_trust_policy(self, role_name):
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        try:
            self.iam_client.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=json.dumps(trust_policy)
            )
            print(f"[INFO] Updated trust policy for role: {role_name}")
            time.sleep(10)
        except ClientError as e:
            print(f"[WARN] Could not update trust policy for role '{role_name}': {e}")
