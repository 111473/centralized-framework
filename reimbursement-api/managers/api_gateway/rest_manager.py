import random
import json
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class RestApiGatewayManager:
    def __init__(self, api_config, stage_config, resource_methods, usage_plan_config,
                 apigateway_client, lambda_client):
        self.api_name = api_config["name"]
        self.lambda_function_name = api_config["lambda_function_name"]
        self.authorizers = api_config.get("authorizers", {})
        self.api_type = api_config.get("api_type", "REST")
        self.api_creation_mode = api_config.get("api_creation_mode", "auto")

        self.region = stage_config["region"]
        self.account_id = stage_config["account_id"]
        self.stage_name = stage_config["stage_name"]
        self.secrets_file = stage_config.get("secrets_file", ".env")

        self.resource_methods = resource_methods
        self.usage_plan_config = usage_plan_config

        self.apigateway = apigateway_client
        self.lambda_client = lambda_client
        self.authorizer_ids = {}

        if self.api_type != "REST":
            raise ValueError(f"Unsupported API type: {self.api_type}. Only 'REST' is supported.")

    def get_or_create_api(self):
        logger.info(f"🔍 Searching for existing REST API: {self.api_name}")
        for api in self.apigateway.get_rest_apis()["items"]:
            if api["name"] == self.api_name:
                if self.api_creation_mode == "new":
                    raise RuntimeError(f"API '{self.api_name}' already exists but 'new' mode was specified.")
                logger.info(f"✅ Using existing REST API: {api['id']}")
                return api["id"]

        if self.api_creation_mode == "reuse":
            raise RuntimeError(f"API '{self.api_name}' not found and 'reuse' mode was specified.")

        new_api = self.apigateway.create_rest_api(name=self.api_name)
        logger.info(f"🚀 Created new REST API: {new_api['id']}")
        return new_api["id"]

    def get_root_resource_id(self, api_id):
        resources = self.apigateway.get_resources(restApiId=api_id)
        return next(item["id"] for item in resources["items"] if item["path"] == "/")

    def create_nested_resource(self, api_id, root_id, resource_path):
        logger.info(f"📁 Creating nested resource for path: {resource_path}")
        current_id = root_id
        path_segments = [segment for segment in resource_path.strip("/").split("/") if segment]

        existing_resources = self.apigateway.get_resources(restApiId=api_id)["items"]
        existing_paths = {res["path"]: res["id"] for res in existing_resources}

        cumulative_path = ""
        for segment in path_segments:
            cumulative_path += f"/{segment}"
            if cumulative_path in existing_paths:
                current_id = existing_paths[cumulative_path]
                logger.debug(f"🔁 Found existing segment: {cumulative_path}")
                continue
            response = self.apigateway.create_resource(
                restApiId=api_id, parentId=current_id, pathPart=segment
            )
            current_id = response["id"]
            logger.info(f"🆕 Created segment: {cumulative_path} -> ID: {current_id}")
        return current_id

    def ensure_cors(self, api_id, resource_id):
        logger.info(f"🌐 Setting up CORS for resource ID: {resource_id}")
        try:
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                authorizationType="NONE"
            )
        except ClientError as e:
            if "ConflictException" not in str(e):
                raise

        cors_headers = {
            "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
            "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PATCH,DELETE,OPTIONS'",
            "method.response.header.Access-Control-Allow-Origin": "'*'"
        }

        try:
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                type="MOCK",
                requestTemplates={"application/json": '{"statusCode": 200}'}
            )
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                statusCode="200",
                responseParameters={k: True for k in cors_headers}
            )
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                statusCode="200",
                responseParameters=cors_headers
            )
            logger.info(f"✅ CORS configured successfully.")
        except ClientError as e:
            if "ConflictException" not in str(e):
                raise

    def setup_lambda_authorizers(self, api_id):
        for key, config in self.authorizers.items():
            name = config["authorizer_function_name"]
            authorizer_type = config.get("type", "TOKEN").upper()
            ttl_seconds = int(config.get("ttl_seconds", 300))
            identity_sources = config.get("identity_source_type") or config.get("identity_source")

            identity_source = (
                ",".join(identity_sources) if isinstance(identity_sources, list) else identity_sources
            )

            lambda_arn = self.lambda_client.get_function(FunctionName=name)["Configuration"]["FunctionArn"]

            try:
                self.lambda_client.add_permission(
                    FunctionName=name,
                    StatementId=f"apigateway-auth-{random.randint(100000, 999999)}",
                    Action="lambda:InvokeFunction",
                    Principal="apigateway.amazonaws.com",
                    SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/authorizers/*"
                )
                logger.info(f"🔐 Permission added for Lambda authorizer: {name}")
            except self.lambda_client.exceptions.ResourceConflictException:
                logger.info(f"⚠️ Permission already exists for Lambda authorizer: {name}")

            response = self.apigateway.create_authorizer(
                restApiId=api_id,
                name=name,
                type=authorizer_type,
                authorizerUri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
                identitySource=identity_source,
                authorizerResultTtlInSeconds=ttl_seconds
            )
            self.authorizer_ids[name] = response["id"]
            logger.info(f"✅ Created Lambda authorizer: {name} (type: {authorizer_type})")

    def setup_or_update_method(self, api_id, resource_id, method, path_part, config):
        logger.info(f"🔧 Setting up method {method} for path /{path_part}")
        authorization_map = config.get("authorization", {})
        request_validator_map = config.get("request_validator", {})

        auth_name = authorization_map.get(method, "NONE")
        auth_type = "CUSTOM" if auth_name in self.authorizer_ids else "NONE"

        method_kwargs = {
            "restApiId": api_id,
            "resourceId": resource_id,
            "httpMethod": method,
            "authorizationType": auth_type
        }

        if auth_type == "CUSTOM":
            method_kwargs["authorizerId"] = self.authorizer_ids[auth_name]

        validator_name = request_validator_map.get(method)
        if validator_name:
            method_kwargs["requestValidatorId"] = self.ensure_request_validator(api_id, validator_name)

        try:
            self.apigateway.put_method(**method_kwargs)
        except ClientError as e:
            if "ConflictException" not in str(e):
                raise

        lambda_arn = self.lambda_client.get_function(FunctionName=self.lambda_function_name)["Configuration"]["FunctionArn"]
        uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"

        try:
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                type="AWS_PROXY",
                integrationHttpMethod="POST",
                uri=uri
            )
        except ClientError:
            pass

        try:
            self.lambda_client.add_permission(
                FunctionName=self.lambda_function_name,
                StatementId=f"apigateway-{random.randint(100000, 999999)}",
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/{method}/{path_part}"
            )
        except self.lambda_client.exceptions.ResourceConflictException:
            pass

    def ensure_request_validator(self, api_id, validator_name):
        validators = self.apigateway.get_request_validators(restApiId=api_id)["items"]
        for v in validators:
            if v["name"] == validator_name:
                return v["id"]

        validate_body = "body" in validator_name.lower()
        validate_params = "params" in validator_name.lower() or "query" in validator_name.lower()

        response = self.apigateway.create_request_validator(
            restApiId=api_id,
            name=validator_name,
            validateRequestBody=validate_body,
            validateRequestParameters=validate_params
        )
        return response["id"]

    def mark_api_key_required(self, api_id, resource_id, method):
        try:
            self.apigateway.update_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                patchOperations=[{
                    "op": "replace",
                    "path": "/apiKeyRequired",
                    "value": "true"
                }]
            )
        except ClientError as e:
            if "BadRequestException" not in str(e):
                raise

    def create_deployment(self, api_id):
        self.apigateway.create_deployment(
            restApiId=api_id,
            stageName=self.stage_name,
            description="Automated deployment"
        )
        logger.info(f"🚀 Created deployment for stage: {self.stage_name}")

    def create_api_key_and_usage_plan(self, api_id):
        api_key = self._get_or_create_api_key()
        usage_plan = self._get_or_create_usage_plan(api_id)
        self._ensure_api_stage_attached(api_id, usage_plan)
        self._link_api_key_to_usage_plan(api_key, usage_plan)
        self._save_api_key(api_key["value"])
        logger.info("🔑 API Key and usage plan setup completed.")

    def _get_or_create_api_key(self):
        name = f"{self.api_name}-key"
        keys = self.apigateway.get_api_keys(nameQuery=name, includeValues=True)["items"]
        return keys[0] if keys else self.apigateway.create_api_key(name=name, enabled=True)

    def _get_or_create_usage_plan(self, api_id):
        name = f"{self.api_name}-usage-plan"
        plans = self.apigateway.get_usage_plans()["items"]
        for plan in plans:
            if plan["name"] == name:
                return plan

        return self.apigateway.create_usage_plan(
            name=name,
            apiStages=[{"apiId": api_id, "stage": self.stage_name}],
            throttle={
                "rateLimit": self.usage_plan_config.get("rate_limit", 100),
                "burstLimit": self.usage_plan_config.get("burst_limit", 20)
            },
            quota={
                "limit": self.usage_plan_config.get("limit", 1000),
                "period": self.usage_plan_config.get("period", "MONTH")
            }
        )

    def _ensure_api_stage_attached(self, api_id, plan):
        attached = any(
            stage["apiId"] == api_id and stage["stage"] == self.stage_name
            for stage in plan.get("apiStages", [])
        )
        if not attached:
            self.apigateway.update_usage_plan(
                usagePlanId=plan["id"],
                patchOperations=[{
                    "op": "add",
                    "path": "/apiStages",
                    "value": f"{api_id}:{self.stage_name}"
                }]
            )

    def _link_api_key_to_usage_plan(self, api_key, usage_plan):
        try:
            self.apigateway.create_usage_plan_key(
                usagePlanId=usage_plan["id"],
                keyId=api_key["id"],
                keyType="API_KEY"
            )
        except ClientError as e:
            if "ConflictException" not in str(e):
                raise

    def _save_api_key(self, value):
        path = Path(self.secrets_file)
        if path.suffix == ".json":
            data = json.load(path.open()) if path.exists() else {}
            data["API_KEY"] = value
            json.dump(data, path.open("w"), indent=2)
        else:
            existing = {}
            if path.exists():
                with path.open() as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            existing[k] = v
            existing["API_KEY"] = value
            with path.open("w") as f:
                for k, v in existing.items():
                    f.write(f"{k}={v}\n")

    def run_setup(self):
        logger.info(f"🚧 Starting setup for REST API Gateway: {self.api_name}")
        api_id = self.get_or_create_api()
        root_id = self.get_root_resource_id(api_id)
        self.setup_lambda_authorizers(api_id)

        for path_key, config in self.resource_methods.items():
            resource_path = config.get("resource_path", f"/{path_key}")
            methods = config.get("methods", [])
            require_api_key = config.get("require_api_key", [])
            cors_enabled = config.get("cors_enabled", False)

            resource_id = self.create_nested_resource(api_id, root_id, resource_path)

            if cors_enabled:
                self.ensure_cors(api_id, resource_id)

            for method in methods:
                if method != "OPTIONS":
                    self.setup_or_update_method(api_id, resource_id, method, path_key, config)
                    if method in require_api_key:
                        self.mark_api_key_required(api_id, resource_id, method)

        self.create_deployment(api_id)
        self.create_api_key_and_usage_plan(api_id)
        logger.info(f"✅ Finished setup for REST API Gateway: {self.api_name}")
