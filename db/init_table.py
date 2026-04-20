import boto3
from botocore.exceptions import ClientError

def create_table():
    try:
        # Connect to DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create table
        table = dynamodb.create_table(
            TableName='iot_data',
            KeySchema=[
                {
                    'AttributeName': 'data_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'data_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        print("Creating table... Please wait")

        table.wait_until_exists()

        print("Table created successfully!")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Table already exists!")
        else:
            print("Error:", e)


if __name__ == "__main__":
    create_table()