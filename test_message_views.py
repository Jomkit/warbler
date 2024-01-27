"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from flask import get_flashed_messages
from models import db, connect_db, Message, User, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.u1 = User.signup('test1', 'test1@gmail.com', 'test1password', None)
        self.u2 = User.signup('test2', 'test2@gmail.com', 'test2password', None)
        self.u3 = User.signup('test3', 'test3@gmail.com', 'test3password', None)
        self.u4 = User.signup('test4', 'test4@gmail.com', 'test4password', None)
        self.u5 = User.signup('test5', 'test5@gmail.com', 'test5password', None)
        self.u6 = User.signup('test6', 'test6@gmail.com', 'test6password', None)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
    
    def setup_follow(self):
        self.testuser.followers.append(self.u1)
        self.testuser.followers.append(self.u2)
        self.testuser.following.append(self.u3)
        self.testuser.following.append(self.u4)
        db.session.commit()

    def setup_likes_msgs(self):
        self.m1 = Message(text='test text', user_id=self.u1.id)        
        self.m2 = Message(text='test text 2', user_id=self.testuser.id)        
        self.m3 = Message(text='test text 3', user_id=self.u2.id)        
        db.session.add_all([self.m1, self.m2, self.m3])
        self.testuser.likes.append(self.m1)
        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_request_context(f'/messages/new'):
            app.preprocess_request()
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                # Now, that session setting is saved, so we can have
                # the rest of ours test

                resp = c.post("/messages/new", data={"text": "Hello"})

                # Make sure it redirects
                self.assertEqual(resp.status_code, 302)

                msg = Message.query.one()
                self.assertEqual(msg.text, "Hello")

    def test_get_add_message_form(self):
        with app.test_request_context(f'/messages/new'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                
                resp = c.get(f'/messages/new')
                
                self.assertEqual(resp.status_code, 200)
                self.assertIn('Add my message!', str(resp.data))

    def test_unauthorized_add_message(self):
        with app.test_request_context(f'/messages/new'):
            app.preprocess_request()
            with app.test_client() as c:
                
                resp = c.post("/messages/new", data={"text": "Hello"})
                
                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)

    def test_show_a_message(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m1.id}'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                
                resp = c.get(f'/messages/{self.m1.id}')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@{self.m1.user.username}', str(resp.data))

    def test_delete_message(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m2.id}/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                
                resp = c.post(f'/messages/{self.m2.id}/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                messages = Message.query.all()
                self.assertNotIn(self.m2, messages)

    def test_delete_message_dne(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/999999/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                
                resp = c.post(f'/messages/999999/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 404)

    def test_delete_message_wrong_user(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m1.id}/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                
                resp = c.post(f'/messages/{self.m1.id}/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)

    def test_delete_message_not_logged_in(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m1.id}/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                
                resp = c.post(f'/messages/{self.m1.id}/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)
    
    def test_add_like(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m3.id}/like'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                resp = c.post(f'/messages/{self.m3.id}/like')

                self.assertEqual(resp.status_code, 302)
                self.assertIn(self.m3, self.testuser.likes) 
                flashed_msgs = get_flashed_messages()
                self.assertIn(f"Liked {self.m3.user.username}'s warble", flashed_msgs)
    
    def test_add_like_msg_dne(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/999999/like'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                resp = c.post(f'/messages/999999/like')

                self.assertEqual(resp.status_code, 404)
    
    def test_add_like_unauthorized(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m3.id}/like'):
            app.preprocess_request()
            with app.test_client() as c:
                
                resp = c.post(f'/messages/{self.m3.id}/like')

                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn(f"Access unauthorized.", flashed_msgs)
    
    def test_remove_like(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m1.id}/like'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                resp = c.post(f'/messages/{self.m1.id}/like')

                self.assertEqual(resp.status_code, 302)
                self.assertNotIn(self.m1, self.testuser.likes) 
                flashed_msgs = get_flashed_messages()
                self.assertIn(f"Unliked {self.m1.user.username}'s warble", flashed_msgs)
    
    def test_remove_like_msg_dne(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/999999/like'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.testuser.id
                resp = c.post(f'/messages/999999/like')

                self.assertEqual(resp.status_code, 404)
    
    def test_remove_like_unauthorized(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/messages/{self.m1.id}/like'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.post(f'/messages/{self.m1.id}/like')

                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn(f"Access unauthorized.", flashed_msgs)