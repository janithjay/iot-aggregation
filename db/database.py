import boto3
from datetime import datetime

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table name
table = dynamodb.Table('IoT_Data')


# 🔹 1. Insert Record
def insert_record(data_id, sensor_id, object_key):
    table.put_item(
        Item={
            'data_id': data_id,
            'sensor_id': sensor_id,
            'object_key': object_key,
            'status': 'pending',
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
    )
    print("Record inserted successfully!")


# 🔹 2. Update Status
def update_record_status(data_id, status):
    table.update_item(
        Key={'data_id': data_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': status}
    )
    print("Status updated!")


# 🔹 3. Update Summary
def update_record_summary(data_id, summary):
    table.update_item(
        Key={'data_id': data_id},
        UpdateExpression="SET summary = :sum, #s = :done",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':sum': summary,
            ':done': 'done'
        }
    )
    print("Summary updated!")


# 🔹 4. Get Single Record
def get_record(data_id):
    response = table.get_item(Key={'data_id': data_id})
    return response.get('Item', None)


# 🔹 5. Get All Records
def list_records():
    response = table.scan()
    return response.get('Items', [])