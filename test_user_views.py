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

    def test_logged_in_starts_following(self):
        """Tests if logged in user can follow someone"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            self.assertEqual=(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('<p>@u2</p>', html)

    def test_logged_out_starts_following(self):
        """Tests if logged in user cannot follow someone"""

        with app.test_client() as c:
            resp = c.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            self.assertEqual=(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)

    def test_logged_in_stops_following(self):
        """Tests if logged in user can unfollow someone"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.following.append(u2)

            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            self.assertEqual=(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertNotIn('<p>@u2</p>', html)

    def test_logged_out_stops_following(self):
        """Tests if logged in user cannot unfollow someone"""

        with app.test_client() as c:
            u1 = User.query.get(self.u1_id)
            u2 = User.query.get(self.u2_id)
            u1.following.append(u2)

            resp = c.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            self.assertEqual=(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)


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
                '<button class="btn btn-primary btn-lg">Sign me up!</button>', html)

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


class UserSignupViewTestCase(UserBaseViewTestCase):

    def test_signup(self):
        """Tests if a user can sign up successfully"""

        with app.test_client() as c:
            num_users = len(User.query.all())
            resp = c.post('/signup', data={'username': "u3", 'email': "u3@email.com",
                          'password': "password"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            self.assertEqual(len(User.query.all()), num_users+1)

            html = resp.get_data(as_text=True)
            self.assertIn(
                '<ul class="list-group" id="messages">', html)

    def test_fail_signup(self):
        """Tests if a user is causing an integrity error with
        invalid credentials and getting to see the sign up form again
        """

        with app.test_client() as c:
            num_users = len(User.query.all())
            resp = c.post('/signup', data={'username': None, 'email': "u3@email.com",
                          'password': "password"})

            self.assertEqual(resp.status_code, 200)

            self.assertEqual(len(User.query.all()), num_users)

            html = resp.get_data(as_text=True)
            self.assertIn(
                '<button class="btn btn-primary btn-lg">Sign me up!</button>', html)

