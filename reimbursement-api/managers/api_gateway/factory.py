from .rest_manager import RestApiGatewayManager
from .http_manager import HttpApiGatewayManager


class ApiGatewayFactory:
    @staticmethod
    def get_manager(protocol_type, **kwargs):
        api_config = kwargs.get("api_config", {})

        # Flatten HTTP integration config
        if "http_invoke" in api_config:
            http_invoke = api_config.pop("http_invoke", {})
            api_config["url"] = http_invoke.get("url")
            api_config["http_method"] = http_invoke.get("http_method")

        # Flatten Lambda integration config
        if "lambda_invoke" in api_config:
            lambda_invoke = api_config.pop("lambda_invoke", {})
            api_config["lambda_function_name"] = lambda_invoke.get("lambda_function_name")
            api_config["invoke_permission"] = lambda_invoke.get("invoke_permission")

        if protocol_type == "HTTP":
            return HttpApiGatewayManager(**kwargs)
        elif protocol_type == "REST":
            return RestApiGatewayManager(**kwargs)
        else:
            raise NotImplementedError(f"Unsupported protocol: {protocol_type}")
