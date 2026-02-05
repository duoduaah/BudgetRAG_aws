import os
import boto3
from. lambda_helpers import upload_folder_to_s3

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
s3_client = session.client("s3")


def upload_to_s3(local_folder):
    if os.path.exists(local_folder):
        count = upload_folder_to_s3(
            s3_client=s3_client,
            local_folder=local_folder,
            s3_prefix=f"input/{local_folder}",
            bucket=os.getenv("S3_BUCKET"),
            file_extensions=[".pdf", ".PDF"]
        )
        print(f"\n Waiting for automatic parsing to complete...")
        print("   (The Lambda function will automatically convert PDFs to markdown)")
    else:
        print(f" Folder not found: {local_folder}")