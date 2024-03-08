"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Model to test our models"""

    def setUp(self):
        """Set up that runs before every test"""

        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        """Tear down that runs after every test"""

        db.session.rollback()

    def test_user_model(self):
        """Tests that users are created correctly"""

        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_following(self):
        """Tests that User method is_following accurately detects if
        a user is following another user"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        result = u1.is_following(u2)
        self.assertTrue(result)

        result2 = u2.is_following(u1)
        self.assertFalse(result2)

    def test_is_followed_by(self):
        """Tests that User method is_followed_by fucntions correctly"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        result = u2.is_followed_by(u1)
        self.assertTrue(result)

        result2 = u1.is_followed_by(u2)
        self.assertFalse(result2)

    def test_signup_success(self):
        """Tests user.signup adds successfully with valid credentials"""

        user = User.signup(
            username="test_user",
            email="test@email.com",
            password="password"
        )

        db.session.commit()

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "test_user")
        self.assertNotEqual(user.password, "password")

    def test_signup_fail(self):
        """Tests if signup fails if the user does not enter valid info"""

        with self.assertRaises(IntegrityError):  # Testing invalid username
            user = User.signup(
                username=None,
                email="test@email.com",
                password="password"
            )
            db.session.commit()

        db.session.rollback()

        with self.assertRaises(IntegrityError):  # Testing invalid email
            user = User.signup(
                username="David",
                email=None,
                password="password"
            )
            db.session.commit()

        db.session.rollback()

        with self.assertRaises(ValueError):  # Testing invalid password
            user = User.signup(
                username="David",
                email="test@email.com",
                password=None
            )
            db.session.commit()

        db.session.rollback()

        with self.assertRaises(IntegrityError):  # Testing an existing username
            user = User.signup(
                username="u1",
                email="test@email.com",
                password="password"
            )
            db.session.commit()

        db.session.rollback()

        with self.assertRaises(IntegrityError):  # Testing an existing email
            user = User.signup(
                username="David",
                email="u1@email.com",
                password="password"
            )
            db.session.commit()

    def test_authenticate(self):
        """Tests if authenticate returns a user successfully with
        valid credentials.
        """

        authenticated_user = User.authenticate("u1", "password")

        self.assertEqual(authenticated_user.id, self.u1_id)


    def test_fail_authenticate(self):
        """Tests if authenticate returns false with invalid credentials."""

        unauthenticated_user = User.authenticate("u1", "notpassword")

        self.assertFalse(unauthenticated_user)

        unauthenticated_user2 = User.authenticate("David", "password")

        self.assertFalse(unauthenticated_user2)

