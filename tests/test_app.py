import json
import unittest
from unittest.mock import MagicMock, patch

# Import the Flask application
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'flask-mongodb-app')))

import app as flask_module

class TestFlaskMongoDBApp(unittest.TestCase):
    def setUp(self):
        self.app = flask_module.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_root_endpoint(self):
        """Test GET / endpoint returns welcome message with current time."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Flask app! The current time is:", response.data)

    @patch.object(flask_module.collection, 'insert_one')
    def test_post_data_endpoint_success(self, mock_insert):
        """Test POST /data endpoint inserts JSON data and returns 201."""
        mock_insert.return_value = MagicMock(inserted_id="fake_id")
        payload = {"sampleKey": "sampleValue"}
        
        response = self.client.post(
            '/data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "Data inserted")
        mock_insert.assert_called_once_with(payload)

    def test_post_data_endpoint_invalid_payload(self):
        """Test POST /data endpoint returns 400 when invalid payload is sent."""
        response = self.client.post(
            '/data',
            data="not a json",
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    @patch.object(flask_module.collection, 'find')
    def test_get_data_endpoint_success(self, mock_find):
        """Test GET /data endpoint returns list of inserted documents excluding _id."""
        mock_docs = [{"sampleKey": "sampleValue1"}, {"sampleKey": "sampleValue2"}]
        mock_find.return_value = mock_docs

        response = self.client.get('/data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["sampleKey"], "sampleValue1")
        mock_find.assert_called_once_with({}, {"_id": 0})

    @patch.object(flask_module.client.admin, 'command')
    def test_healthz_healthy(self, mock_command):
        """Test GET /healthz endpoint returns 200 when MongoDB ping succeeds."""
        mock_command.return_value = {"ok": 1}
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("database"), "connected")

    @patch.object(flask_module.client.admin, 'command')
    def test_healthz_unhealthy(self, mock_command):
        """Test GET /healthz endpoint returns 503 when MongoDB ping fails."""
        mock_command.side_effect = Exception("Connection timed out")
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "unhealthy")
        self.assertEqual(data.get("database"), "disconnected")

if __name__ == '__main__':
    unittest.main()
