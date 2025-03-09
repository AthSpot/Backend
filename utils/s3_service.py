import boto3
import uuid
from typing import BinaryIO, Optional, Dict, Any
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
import os
from urllib.parse import urlparse

# AWS S3 configuration
S3_BUCKET_NAME = "your-s3-bucket-name"  # Replace with your bucket name
S3_REGION = "your-aws-region"  # e.g., "us-east-1"
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/"

# Initialize S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)


def generate_file_key(file_prefix: str, file_name: str) -> str:
    """Generate a unique key for storing file in S3"""
    # Generate a UUID to ensure uniqueness
    unique_id = str(uuid.uuid4())

    # Clean and extract file extension
    _, file_extension = os.path.splitext(file_name)

    # Create the file key
    return f"{file_prefix}/{unique_id}{file_extension}"


async def upload_file_to_s3(
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        file_prefix: str = "uploads",
        public: bool = True,
        metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Upload a file to AWS S3 bucket

    Args:
        file_content: File content as a file-like object
        file_name: Original file name
        content_type: MIME type of the file
        file_prefix: Folder prefix for the file in S3
        public: Whether the file should be publicly accessible
        metadata: Additional metadata for the file

    Returns:
        Dictionary with file information
    """
    try:
        # Generate a unique file key
        file_key = generate_file_key(file_prefix, file_name)

        # Set extra args
        extra_args = {
            "ContentType": content_type
        }

        # Set ACL if file should be public
        if public:
            extra_args["ACL"] = "public-read"

        # Add metadata if provided
        if metadata:
            extra_args["Metadata"] = metadata

        # Upload file to S3
        s3_client.upload_fileobj(
            file_content,
            S3_BUCKET_NAME,
            file_key,
            ExtraArgs=extra_args
        )

        # Generate the file URL
        file_url = f"{S3_BASE_URL}{file_key}"

        return {
            "key": file_key,
            "url": file_url,
            "file_name": file_name,
            "content_type": content_type
        }

    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file to S3: {str(e)}"
        )


async def delete_file_from_s3(file_url: str) -> bool:
    """
    Delete a file from AWS S3 bucket

    Args:
        file_url: URL of the file to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract file key from URL
        parsed_url = urlparse(file_url)
        file_key = parsed_url.path.lstrip('/')

        # Delete the file
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key
        )

        return True

    except ClientError as e:
        print(f"Error deleting file from S3: {str(e)}")
        return False


async def generate_presigned_url(file_key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for a file in S3

    Args:
        file_key: S3 key for the file
        expiration: URL expiration in seconds (default: 1 hour)

    Returns:
        Presigned URL
    """
    try:
        # Generate the presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': file_key
            },
            ExpiresIn=expiration
        )

        return presigned_url

    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating presigned URL: {str(e)}"
        )