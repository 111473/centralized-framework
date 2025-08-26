import logging
import random
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class HttpApiGatewayManager:
    def __init__(self, api_config, stage_config, resource_methods,
                 usage_plan_config, apigateway_client, lambda_client):
        self.api_config = api_config
        self.name = api_config["name"]
        self.region = stage_config["region"]
        self.account_id = stage_config["account_id"]
        self.stage_name = stage_config["stage_name"]

        self.routes = api_config.get("routes", {})
        self.cors = {
            "AllowOrigins": api_config.get("cors", {}).get("allow_origins", ["*"]),
            "AllowMethods": api_config.get("cors", {}).get("allow_methods", ["GET", "POST"]),
            "AllowHeaders": api_config.get("cors", {}).get("allow_headers", ["Authorization", "Content-Type"]),
            "MaxAge": api_config.get("cors", {}).get("max_age", 3600)
        }
        self.authorizers = {
            k: v for k, v in api_config.get("authorizers", {}).items()
            if isinstance(v, dict)
        }
        self.usage_plan = usage_plan_config

        self.apigatewayv2 = apigateway_client
        self.lambda_client = lambda_client
        self.api_id = None
        self.integration_id = None
        self.authorizer_ids = {}
        self.created_cors_routes = set()

    def run_setup(self):
        logger.info(f"🚀 Starting setup for HTTP API: {self.name}")
        self.api_id = self.create_http_api()

        if self.api_config.get("integration_target") == "HTTP URI":
            self.integration_id = self.create_http_proxy_integration()
        elif self.api_config.get("integration_target") == "LAMBDA":
            self.integration_id = self.create_lambda_integration()

        self.create_authorizers()
        self.create_routes()
        self.create_stage()

    def create_http_api(self):
        existing = self.apigatewayv2.get_apis()["Items"]
        for api in existing:
            if api["Name"] == self.name:
                logger.info(f"Using existing HTTP API: {api['ApiId']}")
                return api["ApiId"]

        result = self.apigatewayv2.create_api(
            Name=self.name,
            ProtocolType="HTTP",
            CorsConfiguration=self.cors
        )
        logger.info(f"✅ Created HTTP API: {result['ApiId']}")
        return result["ApiId"]

    def create_lambda_integration(self):
        lambda_name = self.api_config.get("lambda_function_name")
        lambda_arn = self.lambda_client.get_function(
            FunctionName=lambda_name
        )["Configuration"]["FunctionArn"]

        uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        response = self.apigatewayv2.create_integration(
            ApiId=self.api_id,
            IntegrationType="AWS_PROXY",
            IntegrationUri=uri,
            PayloadFormatVersion="2.0"
        )

        logger.info(f"✅ Created Lambda integration: {response['IntegrationId']}")
        return response["IntegrationId"]

    def create_http_proxy_integration(self):
        url = self.api_config.get("url")
        method = self.api_config.get("http_method", "GET")

        if not url:
            logger.error(f"[{self.name}] Missing 'url' for HTTP URI integration.")
            raise ValueError("HTTP URI integration target requires 'url' key at the root level.")

        response = self.apigatewayv2.create_integration(
            ApiId=self.api_id,
            IntegrationType="HTTP_PROXY",
            IntegrationUri=url,
            IntegrationMethod=method,
            PayloadFormatVersion="1.0"
        )

        logger.info(f"✅ Created HTTP_PROXY integration: {response['IntegrationId']}")
        return response["IntegrationId"]

    def create_authorizers(self):
        for name, config in self.authorizers.items():
            auth_type = config.get("type", "LAMBDA").upper()
            identity_source = config.get("identity_source", "$request.header.Authorization")
            ttl = config.get("ttl_seconds", 300)

            if auth_type == "JWT":
                result = self.apigatewayv2.create_authorizer(
                    ApiId=self.api_id,
                    Name=name,
                    AuthorizerType="JWT",
                    IdentitySource=[identity_source],
                    JwtConfiguration={
                        "Issuer": config["issuer"],
                        "Audience": config["audience"]
                    },
                    AuthorizerResultTtlInSeconds=ttl
                )
                self.authorizer_ids[name] = result["AuthorizerId"]
                logger.info(f"✅ Created JWT Authorizer: {name}")

            elif auth_type == "LAMBDA":
                lambda_name = config["authorizer_function_name"]
                response_mode = config.get("response_mode", "simple").lower()

                lambda_arn = self.lambda_client.get_function(FunctionName=lambda_name)["Configuration"]["FunctionArn"]

                try:
                    self.lambda_client.add_permission(
                        FunctionName=lambda_name,
                        StatementId=f"apigw-auth-{random.randint(100000, 999999)}",
                        Action="lambda:InvokeFunction",
                        Principal="apigateway.amazonaws.com",
                        SourceArn=f"arn:aws:execute-api:{self.region}:{self.account_id}:{self.api_id}/authorizers/*"
                    )
                except self.lambda_client.exceptions.ResourceConflictException:
                    pass

                result = self.apigatewayv2.create_authorizer(
                    ApiId=self.api_id,
                    Name=name,
                    AuthorizerType="REQUEST",
                    AuthorizerUri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
                    IdentitySource=[identity_source],
                    AuthorizerResultTtlInSeconds=ttl,
                    AuthorizerPayloadFormatVersion="2.0",
                    EnableSimpleResponses=(response_mode == "simple")
                )
                self.authorizer_ids[name] = result["AuthorizerId"]
                logger.info(f"✅ Created Lambda Authorizer ({response_mode}): {name}")

            else:
                logger.warning(f"⚠️ Unknown authorizer type: {auth_type} for {name}")

    def create_routes(self):
        for path, cfg in self.routes.items():
            for method in cfg.get("methods", []):
                route_key = f"{method} /{path}"
                auth_name = cfg.get("authorization", {}).get(method)

                route_kwargs = {
                    "ApiId": self.api_id,
                    "RouteKey": route_key,
                    "Target": f"integrations/{self.integration_id}" if self.integration_id else None
                }

                if auth_name and auth_name in self.authorizer_ids:
                    route_kwargs["AuthorizerId"] = self.authorizer_ids[auth_name]
                    route_kwargs["AuthorizationType"] = "CUSTOM"
                elif auth_name:
                    logger.warning(f"⚠️ Authorizer '{auth_name}' not found for route: {route_key}")

                try:
                    self.apigatewayv2.create_route(**{k: v for k, v in route_kwargs.items() if v is not None})
                    logger.info(f"✅ Created route: {route_key} (auth: {auth_name or 'NONE'})")
                except self.apigatewayv2.exceptions.ConflictException:
                    logger.info(f"⚠️ Route already exists: {route_key}")

                if cfg.get("cors_enabled"):
                    self.create_cors_preflight_route(path)

    def create_cors_preflight_route(self, path):
        if path in self.created_cors_routes:
            return

        route_key = f"OPTIONS /{path}"
        try:
            self.apigatewayv2.create_route(
                ApiId=self.api_id,
                RouteKey=route_key,
                Target=f"integrations/{self.integration_id}"
            )
            logger.info(f"✅ Created CORS preflight route: {route_key}")
            self.created_cors_routes.add(path)
        except self.apigatewayv2.exceptions.ConflictException:
            logger.info(f"⚠️ CORS preflight route already exists: {route_key}")

    def create_stage(self):
        try:
            self.apigatewayv2.create_stage(
                ApiId=self.api_id,
                StageName=self.stage_name,
                AutoDeploy=True
            )
            logger.info(f"✅ Created stage: {self.stage_name}")
        except self.apigatewayv2.exceptions.ConflictException:
            logger.info(f"⚠️ Stage already exists: {self.stage_name}")
