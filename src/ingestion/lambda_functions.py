import os
import boto3
from lambda_helpers import * 

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

env_vars = {
    "VISION_AGENT_API_KEY": os.getenv("VISION_AGENT_API_KEY"),
    "ADE_MODEL": os.getenv("ADE_MODEL"),
    "INPUT_FOLDER": "input/",
    "OUTPUT_FOLDER": "output/",
    "S3_BUCKET": os.getenv("S3_BUCKET"),
    "FORCE_REPROCESS": "false" 
}

s3_client = session.client("s3")
iam = session.client("iam")
lambda_client = session.client("lambda")


def create_deploy_lambda():
    source_files = ["ade_s3_handler.py"]
    requirements = ["pydantic", "landingai-ade", "typing-extensions"]

    zip_path = create_deployment_package(
        source_files=source_files,
        requirements=requirements,
        output_zip="../ade_lambda.zip",
        package_dir="ade_package"
    )

    role_arn = create_or_update_lambda_role(
    iam_client=iam,
    role_name="lambda-ade-exec-role",
    description="Execution role for LandingAI ADE Lambda"
    )

    deploy_lambda_function(
    lambda_client=lambda_client,
    function_name="ade-s3-handler",
    zip_file="../ade_lambda.zip",
    role_arn=role_arn,
    handler="ade_s3_handler.ade_handler",
    env_vars=env_vars,
    runtime="python3.10",
    timeout=900,
    memory_size=1024
    )


def setup_trigger():
    setup_s3_trigger(
    s3_client=s3_client,
    lambda_client=lambda_client,
    bucket=os.getenv("S3_BUCKET"),
    prefix="input/",
    function_name="ade-s3-handler",
    suffix=".pdf"
)


