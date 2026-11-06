import json, os, tempfile, threading, unittest, urllib.request, urllib.error
from http.server import ThreadingHTTPServer
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main

class WorkflowSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        main.DB_PATH = os.path.join(cls.tmp.name, "test.db")
        main.TOKENS.clear()
        main.init_db()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), main.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.tmp.cleanup()

    def call(self, path, method="GET", payload=None, token=None):
        data = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "Content-Type":"application/json", **({"Authorization":f"Bearer {token}"} if token else {})})
        with urllib.request.urlopen(req) as res: return res.status, json.loads(res.read())

    def test_team_leader_employee_review_flow(self):
        status, health = self.call("/api/health")
        self.assertEqual(status, 200); self.assertEqual(health["status"], "ok")
        _, leader = self.call("/api/login", "POST", {"email":"lead@flowmetrics.local", "password":"FlowMetrics@123"})
        _, employee = self.call("/api/login", "POST", {"email":"employee@flowmetrics.local", "password":"FlowMetrics@123"})
        _, people = self.call("/api/users", token=leader["token"])
        self.assertTrue(people)
        _, task = self.call("/api/tasks", "POST", {"title":"Test assignment", "description":"Smoke test", "assignee_id":people[0]["id"], "priority":"High"}, leader["token"])
        _, assigned = self.call("/api/tasks", token=employee["token"])
        self.assertTrue(any(t["id"] == task["id"] for t in assigned))
        _, submitted = self.call(f"/api/tasks/{task['id']}/update", "PATCH", {"status":"Submitted", "employee_update":"Work completed"}, employee["token"])
        self.assertEqual(submitted["status"], "Submitted")
        _, reviewed = self.call(f"/api/tasks/{task['id']}/review", "PATCH", {"status":"Reviewed", "review_note":"Approved"}, leader["token"])
        self.assertEqual(reviewed["status"], "Reviewed")
        self.assertEqual(reviewed["review_note"], "Approved")

if __name__ == "__main__": unittest.main()
