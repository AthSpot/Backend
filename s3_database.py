import boto3
import json
import os
from botocore.exceptions import ClientError


class S3Database:
    def __init__(self, bucket_name, region_name='us-east-1'):
        """
        Initialize S3 database connection

        Args:
            bucket_name (str): AWS S3 bucket name to use for storage
            region_name (str): AWS region name
        """
        self.s3 = boto3.resource('s3', region_name=region_name)
        self.bucket_name = bucket_name

        # Create bucket if it doesn't exist
        try:
            self.s3.meta.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            # Bucket doesn't exist or you don't have access
            self.s3.create_bucket(Bucket=bucket_name)

    def save_data(self, key, data):
        """
        Save data to S3

        Args:
            key (str): Unique identifier for the data
            data (dict): Data to save
        """
        json_data = json.dumps(data)
        self.s3.Object(self.bucket_name, f"{key}.json").put(Body=json_data)

    def load_data(self, key):
        """
        Load data from S3

        Args:
            key (str): Unique identifier for the data

        Returns:
            dict: Data loaded from S3, or None if key doesn't exist
        """
        try:
            obj = self.s3.Object(self.bucket_name, f"{key}.json")
            data = json.loads(obj.get()['Body'].read())
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def delete_data(self, key):
        """
        Delete data from S3

        Args:
            key (str): Unique identifier for the data to delete
        """
        self.s3.Object(self.bucket_name, f"{key}.json").delete()

    def list_keys(self, prefix=""):
        """
        List all keys in the bucket with given prefix

        Args:
            prefix (str): Optional prefix to filter keys

        Returns:
            list: List of keys without .json extension
        """
        keys = []
        bucket = self.s3.Bucket(self.bucket_name)

        for obj in bucket.objects.filter(Prefix=prefix):
            if obj.key.endswith('.json'):
                keys.append(obj.key[:-5])  # Remove .json extension

        return keys