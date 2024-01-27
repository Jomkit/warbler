"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test User Model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        self.u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(self.u)
        db.session.commit()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = self.u

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(str(u), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_user_follows(self):
        """Do is_followed_by and is_following functions behave correctly?"""
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(u2)
        self.u.followers.append(u2) # u2 is a follower of u
        db.session.commit()

        self.assertTrue(self.u.is_followed_by(u2)) # u followed by u2
        self.assertTrue(u2.is_following(self.u)) # u2 follows u

        self.assertFalse(u2.is_followed_by(self.u))
        self.assertFalse(self.u.is_following(u2))

    def test_user_signup(self):
        """ Does user.signup successfully create new user given valid credentials?"""

        test_user = User.signup('testusername', 'testemail@gmail.com', 'testpassword', None)
        db.session.commit()

        self.assertIsInstance(test_user, User)
        self.assertEqual(str(test_user), f"<User #{test_user.id}: {test_user.username}, {test_user.email}>")
        self.assertEqual(test_user.image_url,"/static/images/default-pic.png")

        # duplicate username, missing username, and missing password
        # should raise IntegrityError
        u2 = User.signup('testuser','test@gmail.com','testpw123',None)
        db.session.add(u2)
        self.assertRaises(exc.IntegrityError, db.session.commit)
        db.session.rollback()

        u3 = User.signup(None,'test@gmail.com','testpw123',None)
        db.session.add(u3)
        self.assertRaises(exc.IntegrityError, db.session.commit)
        db.session.rollback()
        self.assertRaises(ValueError, User.signup, 'testperson','test@gmail.com', None, None)

    def test_authenticate(self):
        """Does User.authenticate successfully authenticate a user given 
        valid credentials?"""
        test_user = User.signup('testusername', 'testemail@gmail.com', 'testpassword', 'https://images.pexels.com/photos/2280571/pexels-photo-2280571.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2')
        test_auth = User.authenticate('testusername', 'testpassword')

        # Test User.authenticate properly generates __repr__
        self.assertEqual(str(test_auth), f"<User #{test_user.id}: {test_user.username}, {test_user.email}>")

        # Check that User.authenticate returns false with invalid credentials
        self.assertFalse(User.authenticate('wronguser', 'testpassword'))
        self.assertFalse(User.authenticate('testusername', 'wrongpassword'))