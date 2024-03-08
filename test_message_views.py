"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()

    def test_add_message_logged_out(self):
        """Tests if logged out user cannot add a message"""

        with app.test_client() as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            result = Message.query.filter_by(text="Hello").all()
            self.assertEqual(len(result), 0)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):

    def test_delete_message(self):
        """Tests if logged in user can delete their own message."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/delete")

            self.assertEqual(resp.status_code, 302)

            result = Message.query.filter_by(text="m1-text").all()

            self.assertEqual(len(result), 0)

    def test_delete_message_logged_out(self):
        """Tests user's ability to delete a message when logged out"""

        with app.test_client() as c:

            resp = c.post(f"/messages/{self.m1_id}/delete")

            self.assertEqual(resp.status_code, 302)

            result = Message.query.filter_by(text="m1-text").all()

            self.assertEqual(len(result), 1)

    def test_delete_other_users_message(self):
        """Test logged in user's ability to delete oterh user's messages"""

        with app.test_client() as c:

            u2 = User.signup("u2", "u2@email.com", "password", None)
            db.session.add(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u2.id

            resp = c.post(f"/messages/{self.m1_id}/delete")

            self.assertEqual(resp.status_code, 302)

            result = Message.query.filter_by(text="m1-text").all()

            self.assertEqual(len(result), 1)

class MessageLikeViewTestCase(MessageBaseViewTestCase):
    """Message like view tests"""

    def test_like_add(self):
        """Test user liking a message"""

        with app.test_client() as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f'/users/like/{self.m1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("m1-text", html)

            num_likes = len(Likes.query.all())
            self.assertEqual(num_likes, 1)

    def test_unlike(self):
        """Tests user unliking a message"""

        with app.test_client() as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            u1 = User.query.get(self.u1_id)
            liked_message = Message.query.get(self.m1_id)
            u1.liked_messages.append(liked_message)


            resp = c.post(f'/users/unlike/{self.m1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertNotIn("m1-text", html)

            num_likes = len(Likes.query.all())
            self.assertEqual(num_likes, 0)
