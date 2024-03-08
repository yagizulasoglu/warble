"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_user_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


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


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id
        db.session.flush()


class UserFollowerViewTestCase(UserBaseViewTestCase):
    def test_logged_in_follower_page(self):
        """Tests if logged in user can see followers page"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/followers")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('<p class="small">Followers</p>', html)

    def test_logged_out_follower_page(self):
        """Tests if logged out user cannot access follower page"""

        with app.test_client() as c:
            resp = c.get(f"/users/{self.u1_id}/followers",
                         follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(
                '<a href="/signup" class="btn btn-primary">Sign up</a>', html)


class UserFollowingViewTestCase(UserBaseViewTestCase):

    def test_logged_in_following_page(self):
        """Tests if logged in user can see following page"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/following")
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('<p class="small">Following</p>', html)

    def test_logged_out_following_page(self):
        """Tests if logged out user cannot access following page"""

        with app.test_client() as c:
            resp = c.get(f"/users/{self.u1_id}/following",
                         follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(
                '<a href="/signup" class="btn btn-primary">Sign up</a>', html)

class UserDeleteViewTestCase(UserBaseViewTestCase):

    def test_delete_user(self):
        """Tests user deleting their account"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/users/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIsNone(User.query.get(self.u1_id))

            html = resp.get_data(as_text=True)
            self.assertIn(
                '<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    def test_delete_user_logged_out(self):
        """Tests delete request when no user is logged in"""

        with app.test_client() as c:

            num_users = len(User.query.all())

            resp = c.post('/users/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertEqual(len(User.query.all()), num_users)

            html = resp.get_data(as_text=True)
            self.assertIn(
                '<a href="/signup" class="btn btn-primary">Sign up</a>', html)

#TODO: tested all question in the instructions.
        #added tests for delete user routes.
        #should look for any other routes to test.