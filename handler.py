
import json
from datetime import datetime

import boto3


dynamodb = boto3.resource("dynamodb")
count_table = dynamodb.Table("VisitorCounts")
log_table = dynamodb.Table("VisitorLog")


def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    path = body.get("path", "/")
    visitor_id = body.get("visitor_id") # uuid + expires + path=/
    date = body.get("date")  # YYYY-MM-DD

    if not visitor_id or not date:
        return {
            "statusCode": 400, 
            "headers": {
                "Access-Control-Allow-Origin": "https://blog.i544c.com",
                "Access-Control-Allow-Credentials": "true"
            },
            "body": "Missing visitor ID or date"
        }

    visit_key = {
        "visitor_id": visitor_id,
        "visit_id": f"{path}#{date}"
    }

    # Check if already visited today
    existing = log_table.get_item(Key=visit_key)
    if "Item" in existing:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Already counted"}),
            "headers": {
                "Access-Control-Allow-Origin": "https://blog.i544c.com",
                "Access-Control-Allow-Credentials": "true"
            }
        }

    # Log the unique visit
    log_table.put_item(Item={
        **visit_key,
        "visited_at": datetime.utcnow().isoformat(),
        "path": path,
    })

    # Increment total and per-path counts
    count_table.update_item(
        Key={"counter_type": "TOTAL", "path": "TOTAL"},
        UpdateExpression="ADD visits :inc",
        ExpressionAttributeValues={":inc": 1}
    )

    count_table.update_item(
        Key={"counter_type": "PATH", "path": path},
        UpdateExpression="ADD visits :inc",
        ExpressionAttributeValues={":inc": 1}
    )

    return {
        "statusCode": 200, 
        "headers": {
            "Access-Control-Allow-Origin": "https://blog.i544c.com",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps({"message": "Unique visit counted"})
    }


def get_visitor_stats(event, context):
    params = event.get("queryStringParameters") or {}
    path = params.get("path", "/")

    try:
        total_result = count_table.get_item(Key={"counter_type": "TOTAL", "path": "TOTAL"})
        path_result = count_table.get_item(Key={"counter_type": "PATH", "path": path})

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "https://blog.i544c.com",
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({
                "path": path,
                "path_visits": int(path_result.get("Item", {}).get("visits", 0)),
                "total_visits": int(total_result.get("Item", {}).get("visits", 0))
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "https://blog.i544c.com",
                "Access-Control-Allow-Credentials": "true"
            },
            "body": json.dumps({"error": str(e)})
        }
