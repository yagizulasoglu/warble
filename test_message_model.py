"""Message model tests."""

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


    def test_message_creation(self):
        """Testing that correct number of messages created"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        message = Message(text="test text", user_id=u1.id)

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(len(u2.messages), 0)

    def test_is_liked_by(self):
        """Tests Message method is_liked_by"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        message = Message(text="test text", user_id=u1.id)
        db.session.add(message)

        u2.liked_messages.append(message)

        db.session.commit()

        result = message.is_liked_by(u2)

        self.assertTrue(result)

        result2 = message.is_liked_by(u1)

        self.assertFalse(result2)