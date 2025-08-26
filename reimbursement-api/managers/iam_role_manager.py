import json
import os
import re
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class IamRoleManager:
    def __init__(self, config, iam_client, account_id=None, region=None, stage=None, extra_vars=None):
        self.config = config
        self.iam = iam_client
        self.account_id = account_id
        self.region = region
        self.stage = stage
        self.extra_vars = extra_vars or {}

    def setup_role(self):
        role_name = self.config["role_name"]
        trust_policy = self._load_trust_policy(role_name)

        self._create_or_get_role(role_name, trust_policy)
        self._attach_managed_policies(role_name)
        self._attach_inline_policies(role_name)

    def _load_trust_policy(self, role_name):
        trust_policy_path = self.config.get("trust_policy_path", f"policies/{role_name}_trust.json")

        if not Path(trust_policy_path).exists():
            raise FileNotFoundError(f"Trust policy file not found: {trust_policy_path}")

        with open(trust_policy_path, "r") as f:
            return json.load(f)

    def _create_or_get_role(self, role_name, trust_policy):
        try:
            self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            logger.info(f"IAM Role '{role_name}' created.")
        except ClientError as e:
            if "EntityAlreadyExists" in str(e):
                logger.info(f"IAM Role '{role_name}' already exists.")
            else:
                logger.error(f"Failed to create role '{role_name}': {e}")
                raise

    def _attach_managed_policies(self, role_name):
        for policy_name, arn in self.config.get("managed_policies", {}).items():
            try:
                self.iam.attach_role_policy(RoleName=role_name, PolicyArn=arn)
                logger.info(f"Attached managed policy '{policy_name}' to role '{role_name}'.")
            except ClientError as e:
                logger.error(f"Error attaching managed policy '{policy_name}': {e}")

    def _attach_inline_policies(self, role_name):
        for name, policy in self.config.get("inline_policies", {}).items():
            logger.info(f"Attaching inline policy '{name}' to role '{role_name}'")

            resource = policy.get("resource")
            if isinstance(resource, str):
                resource = self._interpolate(resource)
            elif isinstance(resource, list):
                resource = [self._interpolate(r) for r in resource]

            policy_doc = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": policy.get("action"),
                        "Resource": resource
                    }
                ]
            }

            try:
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=name,
                    PolicyDocument=json.dumps(policy_doc)
                )
                logger.info(f"Attached inline policy: {name}")
            except ClientError as e:
                logger.error(f"Failed to attach inline policy '{name}': {e}")

            if self.config.get("debug", False):
                debug_path = f"debug_{role_name}_{name}.json"
                with open(debug_path, "w") as f:
                    json.dump(policy_doc, f, indent=2)
                logger.debug(f"Wrote inline policy to {debug_path}")

    def _interpolate(self, value: str) -> str:
        if not isinstance(value, str):
            return value

        # Core variables
        variables = {
            "account_id": self.account_id or "",
            "region": self.region or "",
            "stage": self.stage or "",
        }
        variables.update(self.extra_vars or {})

        # Populate with environment vars if not present
        for match in re.findall(r"{(\w+)}", value):
            if match not in variables:
                env_val = os.getenv(match)
                if env_val:
                    variables[match] = env_val

        # Replace placeholders
        result = value
        for key, val in variables.items():
            result = result.replace(f"{{{key}}}", str(val))

        # Fail if any unresolved placeholders remain
        unresolved = re.findall(r"{(\w+)}", result)
        if unresolved:
            raise ValueError(
                f"Unresolved placeholders in IAM policy string: '{value}' — missing keys: {unresolved}"
            )

        return result
