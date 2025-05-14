import json
import boto3
import urllib3
import os
from boto3.dynamodb.conditions import Key

# Environment variables
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
# SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:115313776894:mystudentportal:9ef92854-c4b2-4e97-aaff-bf30b0bbe4ac'

# Clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
http = urllib3.PoolManager()

# DynamoDB Table
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def send_slack_notification(student):
    message = f":tada: *New Student Registered!*\n*ID:* {student.get('studentID')}\n*Name:* {student.get('firstName')} {student.get('lastName')}"
    payload = {
        "text": message
    }

    try:
        response = http.request(
            "POST",
            SLACK_WEBHOOK_URL,
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        print("Slack notification sent:", response.status)
    except Exception as e:
        print("Slack notification failed:", e)

def send_sns_notification(student):
    message = f"New student has been registered:\n\nID: {student.get('studentID')}\nName: {student.get('firstName')} {student.get('lastName')}"
    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="New Student Registration"
        )
        print("SNS notification sent. Message ID:", response['MessageId'])
    except Exception as e:
        print("SNS notification failed:", e)

    message = f"New student has been registered:\n\nID: {student.get('studentID')}\nName: {student.get('firstName')} {student.get('lastName')}"
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="New Student Registration"
        )
        print("SNS notification sent.")
    except Exception as e:
        print("SNS notification failed:", e)

def lambda_handler(event, context):
    method = event['httpMethod']

    if method == "POST":
        body = json.loads(event['body'])

        # Store student in DynamoDB
        table.put_item(Item=body)

        # Send notifications
        send_slack_notification(body)
        send_sns_notification(body)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps("Student registered successfully")
        }

    elif method == "GET":
        student_id = event['pathParameters']['studentID']
        response = table.get_item(Key={'studentID': student_id})
        item = response.get('Item')
        if item:
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(item)
            }
        else:
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps("Student not found")
            }

    return {
        "statusCode": 400,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps("Unsupported method")
    }
