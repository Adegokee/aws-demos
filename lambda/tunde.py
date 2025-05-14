import json
import boto3
import urllib3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
http = urllib3.PoolManager()

# Load environment variables
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

# Reference the table
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def send_slack_notification(message):
    try:
        payload = {"text": message}
        encoded_data = json.dumps(payload).encode('utf-8')
        response = http.request(
            'POST',
            SLACK_WEBHOOK_URL,
            body=encoded_data,
            headers={'Content-Type': 'application/json'}
        )
        return response.status == 200
    except Exception as e:
        print("Slack notification error:", str(e))
        return False

def send_sns_notification(message):
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='New Student Registration'
        )
        return response
    except Exception as e:
        print("SNS publish error:", str(e))
        return None

def lambda_handler(event, context):
    method = event['httpMethod']

    if method == "POST":
        try:
            body = json.loads(event['body'])
            table.put_item(Item=body)

            # Prepare notification message
            student_name = f"{body.get('firstName', '')} {body.get('lastName', '')}".strip()
            message = f":tada: A new student has registered: {student_name}!"

            # Send notifications
            send_slack_notification(message)
            send_sns_notification(message)

            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps("Student registered successfully")
            }
        except Exception as e:
            print("Error during POST:", str(e))
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps("Failed to register student")
            }

    elif method == "GET":
        try:
            path_params = event.get('pathParameters') or {}
            student_id = path_params.get('studentID')
            if not student_id:
                return {
                    "statusCode": 400,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps("Missing studentID in path")
                }

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

        except Exception as e:
            print("Error during GET:", str(e))
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps("Error retrieving student data")
            }

    return {
        "statusCode": 400,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps("Unsupported method")
    }
