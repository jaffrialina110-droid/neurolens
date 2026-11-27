import sqlite3
import unittest

from modules.neurosocial import (
    initialize_neurosocial, send_friend_request, respond_to_friend_request,
    list_friend_requests, list_friends, search_people, remove_friend,
    block_user, unblock_user, set_friend_request_privacy, report_user,
)


class NeuroSocialTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE users (
            id TEXT PRIMARY KEY, username TEXT UNIQUE, email TEXT,
            display_name TEXT, active INTEGER DEFAULT 1
        )""")
        self.db.executemany(
            "INSERT INTO users(id,username,email,display_name,active) VALUES (?,?,?,?,1)",
            [("u1","ayna","a@x.test","Ayna"),("u2","sam","s@x.test","Sam"),("u3","lee","l@x.test","Lee")]
        )
        initialize_neurosocial(self.db)

    def tearDown(self):
        self.db.close()

    def test_request_accept_and_friends_list(self):
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"sent")
        incoming=list_friend_requests(self.db,"u2","incoming")
        self.assertEqual(len(incoming),1)
        self.assertFalse(respond_to_friend_request(self.db,"u1",incoming[0]["id"],True))
        self.assertTrue(respond_to_friend_request(self.db,"u2",incoming[0]["id"],True))
        self.assertEqual([x["id"] for x in list_friends(self.db,"u1")],["u2"])

    def test_duplicate_and_reverse_pending(self):
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"sent")
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"already_pending")
        self.assertEqual(send_friend_request(self.db,"u2","u1"),"incoming_pending")

    def test_decline_allows_later_new_request(self):
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"sent")
        req=list_friend_requests(self.db,"u2")[0]
        self.assertTrue(respond_to_friend_request(self.db,"u2",req["id"],False))
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"sent")

    def test_privacy_and_search(self):
        set_friend_request_privacy(self.db,"u2",False)
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"not_accepting")
        self.assertEqual(search_people(self.db,"u1","Sa"),[])

    def test_block_prevents_requests_and_hides_person(self):
        self.assertTrue(block_user(self.db,"u1","u2"))
        self.assertEqual(send_friend_request(self.db,"u2","u1"),"unavailable")
        self.assertEqual(search_people(self.db,"u1","Sa"),[])
        self.assertTrue(unblock_user(self.db,"u1","u2"))

    def test_remove_friend_and_report(self):
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"sent")
        req=list_friend_requests(self.db,"u2")[0]
        self.assertTrue(respond_to_friend_request(self.db,"u2",req["id"],True))
        self.assertTrue(remove_friend(self.db,"u1","u2"))
        self.assertEqual(list_friends(self.db,"u1"),[])
        self.assertTrue(report_user(self.db,"u1","u2","spam","Test report"))
        self.assertFalse(report_user(self.db,"u1","u2","invalid"))

    def test_self_and_inactive_targets_are_rejected(self):
        self.assertEqual(send_friend_request(self.db,"u1","u1"),"invalid")
        self.db.execute("UPDATE users SET active=0 WHERE id='u2'")
        self.db.commit()
        self.assertEqual(send_friend_request(self.db,"u1","u2"),"unavailable")


if __name__ == "__main__":
    unittest.main()
