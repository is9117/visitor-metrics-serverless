import os
import time
import uuid
import requests
import boto3
import unittest
from datetime import datetime, UTC
from urllib.parse import urljoin

# Endpoints for the deployed service
API_BASE = "https://api.i544c.com/"
DYNAMODB_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
COUNT_TABLE = os.getenv("COUNT_TABLE", "VisitorCounts")
LOG_TABLE = os.getenv("LOG_TABLE", "VisitorLog")

session = requests.Session()
dynamodb = boto3.resource("dynamodb", region_name=DYNAMODB_REGION)
count_table = dynamodb.Table(COUNT_TABLE)
log_table = dynamodb.Table(LOG_TABLE)
session = requests.Session()


class TestVisitorServiceIntegration(unittest.TestCase):

    def test_post_and_verify_count(self):
        path = "/test"
        visitor_id = str(uuid.uuid4())
        date = datetime.now(UTC).strftime("%Y-%m-%d")
        url = urljoin(API_BASE, "count")

        payload = {
            "path": path,
            "visitor_id": visitor_id,
            "date": date
        }
        post_headers = {"Content-Type": "application/json"}

        r = session.post(url, json=payload, headers=post_headers)
        self.assertEqual(r.status_code, 200)
        time.sleep(1)

        count_item = count_table.get_item(Key={"counter_type": "PATH", "path": path}).get("Item", {})
        total_item = count_table.get_item(Key={"counter_type": "TOTAL", "path": "TOTAL"}).get("Item", {})
        log_item = log_table.get_item(Key={"visitor_id": visitor_id, "visit_id": f"{path}#{date}"}).get("Item", {})

        self.assertGreater(count_item.get("visits", 0), 0)
        self.assertGreater(total_item.get("visits", 0), 0)
        self.assertEqual(log_item.get("visit_id"), f"{path}#{date}")

    def test_post_then_get_stats(self):
        path = "/test-post-then-get"
        visitor_id = str(uuid.uuid4())
        date = datetime.now(UTC).strftime("%Y-%m-%d")

        # Step 1: POST to record a visit
        post_url = urljoin(API_BASE, "count")
        post_payload = {
            "path": path,
            "visitor_id": visitor_id,
            "date": date
        }
        post_headers = {"Content-Type": "application/json"}
        r_post = session.post(post_url, json=post_payload, headers=post_headers)
        self.assertEqual(r_post.status_code, 200, r_post.text)
        time.sleep(1)  # wait for eventual consistency in DynamoDB

        # Step 2: GET to verify the recorded visit
        get_url = urljoin(API_BASE, f"count?path={path}")
        r_get = session.get(get_url)
        self.assertEqual(r_get.status_code, 200, r_get.text)

        body = r_get.json()
        self.assertEqual(body["path"], path)
        self.assertIn("path_visits", body)
        self.assertIn("total_visits", body)
        self.assertIsInstance(body["path_visits"], int)
        self.assertIsInstance(body["total_visits"], int)
        self.assertGreaterEqual(body["path_visits"], 1)
        self.assertGreaterEqual(body["total_visits"], 1)

    def test_cloudfront_cache_behavior(self):
        path = "/test"
        visitor_id = str(uuid.uuid4())
        url = urljoin(API_BASE, f"count?path={path}")

        headers = {"Cookie": f"visitor_id={visitor_id}"}

        r = session.get(url, headers=headers)
        self.assertEqual(r.status_code, 200, r.content)


if __name__ == "__main__":
    unittest.main()
