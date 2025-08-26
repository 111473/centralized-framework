import tomllib  # For Python 3.11+. Use `tomli` for earlier versions


class ConfigValidationError(Exception):
    pass


def validate_api_config(api_name, api_config):
    required_keys = ["name", "api_type"]
    for key in required_keys:
        if key not in api_config:
            raise ConfigValidationError(f"[apis.{api_name}] is missing required key: '{key}'")

    api_type = api_config.get("api_type", "").upper()
    integration_target = api_config.get("integration_target", "")

    if api_type == "HTTP":
        if "integration_target" not in api_config:
            raise ConfigValidationError(f"[apis.{api_name}] is missing required key: 'integration_target'")

        if integration_target == "HTTP URI":
            if "url" not in api_config:
                raise ConfigValidationError(
                    f"[apis.{api_name}] 'HTTP URI' integration requires 'url' key at root level"
                )

        elif integration_target == "LAMBDA":
            if "lambda_function_name" not in api_config:
                raise ConfigValidationError(
                    f"[apis.{api_name}] 'LAMBDA' integration requires 'lambda_function_name' at root level"
                )

        else:
            raise ConfigValidationError(
                f"[apis.{api_name}] integration_target must be 'HTTP URI' or 'LAMBDA'"
            )


def load_config(file_path="config.toml", stage="dev"):
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    config = {}

    stage_config = data.get("stages", {}).get(stage, {})
    config["stage"] = stage_config

    stage_vars = data.get("variables", {}).get(stage, {})
    config["stage"].update(stage_vars)

    config["iam_roles"] = data.get("iam_roles", {})
    config["apis"] = data.get("apis", {})

    for api_name, api_cfg in config["apis"].items():
        validate_api_config(api_name, api_cfg)

    return config
