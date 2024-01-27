"""Message model tests"""

# run these test like:
#
# python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows
from datetime import datetime

# Set up env. variable to use test database
# set up before before importing our app
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()
class MessageModelTestCase(TestCase):
    """Test message Model"""

    def setUp(self):
        """Create test client, add sample data"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        
        self.test = User.signup('testuser', 'test@gmail.com', 'testpassword', None)
        db.session.commit()

        self.client = app.test_client()

    def test_message_model(self):
        """Does the basic message model work?"""

        msg = Message(text='test', timestamp=None, user_id=self.test.id)
        self.test.messages.append(msg)
        db.session.add(msg)
        db.session.commit()
        
        #msg is instance of Message Class
        self.assertIsInstance(msg, Message)
        self.assertEqual(str(msg), f"<Message {msg.id}>")
        # msg.user is instance of User Class
        self.assertIsInstance(msg.user, User)
        self.assertEqual(str(self.test), f"<User #{self.test.id}: {self.test.username}, {self.test.email}>")
        self.assertIsInstance(msg.timestamp, datetime)
