"""User view routes tests"""
import os
from unittest import TestCase
from flask import g, get_flashed_messages
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

from app import app, CURR_USER_KEY
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db.create_all()

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

class UserSignupLoginTestCase(TestCase):
    """Test User Views"""
    def setUp(self):
        """Create test client, add sample data"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.test = User.signup('testuser', 'test@gmail.com', 'testpassword', None)
        self.u1 = User.signup('test1', 'test1@gmail.com', 'test1password', None)
        self.u2 = User.signup('test2', 'test2@gmail.com', 'test2password', None)
        self.u3 = User.signup('test3', 'test3@gmail.com', 'test3password', None)
        self.u4 = User.signup('test4', 'test4@gmail.com', 'test4password', None)
        self.u5 = User.signup('test5', 'test5@gmail.com', 'test5password', None)
        self.u6 = User.signup('test6', 'test6@gmail.com', 'test6password', None)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
            
    def test_homepage(self):
        with app.test_client() as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h1>What's Happening?</h1>", html)

    def test_get_signup(self):
        with app.test_client() as c:
            resp = c.get('/signup')

            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', str(resp.data))

    def test_post_signup(self):
        with app.test_request_context('/signup'):
            app.preprocess_request()
            with app.test_client() as c: 
                resp = c.post('/signup', follow_redirects=True, 
                            data={'username':'test',
                                    'email':'testemail@gmail.com',
                                    'password':'testpassword',
                                    'image-url': None})
                self.assertEqual(resp.status_code, 200)

    def test_post_signup_invalid_username(self):
        with app.test_request_context('/signup'):
            app.preprocess_request()
            with app.test_client() as c: 
                resp = c.post('/signup', follow_redirects=True, 
                            data={'username':'test1',
                                    'email':'testemail@gmail.com',
                                    'password':'testpassword',
                                    'image-url': None})

                self.assertEqual(resp.status_code, 200)
                flashed_messages = get_flashed_messages()
                self.assertIn('Username already taken', flashed_messages)
                

    def test_get_login(self):
        with app.test_client() as c:
            resp = c.get('/login')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.', str(resp.data))

    def test_post_login(self):
        with app.test_request_context('/login'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.post('/login', data={'username': self.test.username, 'password': 'testpassword'})

                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn(f'Hello, {self.test.username}!', flashed_msgs)

###########################################################
            # User view route tests
class UserViewsTestCase(TestCase):
    """Test User Views"""
    def setUp(self):
        """Create test client, add sample data"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.test = User.signup('testuser', 'test@gmail.com', 'testpassword', None)
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
        self.test.followers.append(self.u1)
        self.test.followers.append(self.u2)
        self.test.following.append(self.u3)
        self.test.following.append(self.u4)
        db.session.commit()

    def setup_likes_msgs(self):
        self.m1 = Message(text='test text', user_id=self.u1.id)        
        self.m2 = Message(text='test text 2', user_id=self.test.id)        
        self.m3 = Message(text='test text 3', user_id=self.u2.id)        
        db.session.add_all([self.m1, self.m2, self.m3])
        self.test.likes.append(self.m1)
        db.session.commit()

    def test_list_users_no_users(self):
        with app.test_client() as c:
            User.query.delete()

            users = User.query.all()
            resp = c.get('/users', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            # in base.html
            self.assertIn('<title>Warbler</title>', html)
            # index.html, when no users
            self.assertEqual(len(users), 0)
   
    def test_list_users(self):
        """Test list_users() list users if there any
    
        in order to access g.user, must create test request context
        additionally we have some functions that execute *before* requests,
        which wouldn't execute unless we use `app.preprocess_request()` below
        """
        with app.test_request_context('/users'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.get('/users')    
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@testuser', html)
                self.assertIn(f'@test1', html)
                self.assertIn(f'@test2', html)
                self.assertIn(f'@test3', html)
                self.assertIn(f'@test4', html)
                self.assertIn(f'@test5', html)
                self.assertIn(f'@test6', html)

    def test_list_users_search(self):
        """Should be able to search users by username
        """
        test_users = [
            User(username='testerguy', password='testpassword',email='testguy@gmail.com'),
            User(username='testergirl', password='testpassword',email='testgirl@gmail.com'),
            User(username='resterman', password='testpassword',email='testman@gmail.com')
        ]
        db.session.add_all(test_users)
        db.session.commit()
        with app.test_request_context('/users'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.get('/users?q=ste')    
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@testerguy', html)
                self.assertIn(f'@testergirl', html)
                self.assertIn(f'@resterman', html)

    def test_show_user_profile(self):
        with app.test_request_context(f'/users/{self.test.id}'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id

                resp = c.get(f'/users/{self.test.id}')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@{self.test.username}', str(resp.data))

    def test_change_password(self):
        with app.test_request_context(f'/users/change-password'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.get('/users/change-password')

                self.assertEqual(resp.status_code, 200)
                self.assertIn('New Password', str(resp.data))

    def test_change_password_success(self):
        with app.test_request_context(f'/users/change-password'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post('/users/change-password', follow_redirects=True,
                              data={'username':self.test.username,
                                    'password':'testpassword',
                                    'new_password': 'testbanana',
                                    'confirm_password': 'testbanana'})

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Password updated successfully', flashed_msgs)
                self.assertIs(User.authenticate(self.test.username, 'testbanana'), self.test)

    def test_change_password_wrong_pw(self):
        with app.test_request_context(f'/users/change-password'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post('/users/change-password', follow_redirects=True,
                              data={'username':self.test.username,
                                    'password':'wrongpassword',
                                    'new_password': 'testbanana',
                                    'confirm_password': 'testbanana'})

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Incorrect credentials', flashed_msgs)

    def test_unauthorized_access(self):
        with app.test_request_context(f'/users/{self.test.id}/followers'):
            app.test_request_context()
            with app.test_client() as c:
                resp = c.get(f'/users/{self.test.id}/followers')
                flashed_msgs = get_flashed_messages()

                self.assertEqual(resp.status_code, 302)
                self.assertIn('Access unauthorized.', flashed_msgs)

    def test_show_user_following(self):
        with app.test_request_context(f'/users/{self.test.id}/following'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                self.setup_follow()
                resp = c.get(f'/users/{self.test.id}/following')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@{self.u3.username}', str(resp.data))
                self.assertIn(f'@{self.u4.username}', str(resp.data))

    def test_show_user_followers(self):
        with app.test_request_context(f'/users/{self.test.id}/followers'):
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                self.setup_follow()
                resp = c.get(f'/users/{self.test.id}/followers')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@{self.u1.username}', str(resp.data))
                self.assertIn(f'@{self.u2.username}', str(resp.data))

    def test_add_to_following(self):
        with app.test_request_context(f'/users/follow/{self.u5.id}'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post(f'/users/follow/{self.u5.id}', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn(self.u5, self.test.following)
                self.assertIn(f'@{self.u5.username}', str(resp.data))

    def test_add_follow_unauthorized(self):
        with app.test_request_context(f'/users/follow/{self.u5.id}'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.post(f'/users/follow/{self.u5.id}', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)

    def test_add_follow_user_dne(self):
        with app.test_request_context(f'/users/follow/999999'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post(f'/users/follow/999999', follow_redirects=True)

                self.assertEqual(resp.status_code, 404)

    def test_stop_following(self):
        self.setup_follow()
        with app.test_request_context(f'/users/stop-following/{self.u3.id}'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post(f'/users/stop-following/{self.u3.id}', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertNotIn(self.u3, self.test.following)
                self.assertNotIn(f'@{self.u3.username}', str(resp.data))

    def test_stop_following_unauthorized(self):
        self.setup_follow()
        with app.test_request_context(f'/users/stop-following/{self.u3.id}'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.post(f'/users/stop-following/{self.u3.id}', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)
    
    def test_stop_following_user_dne(self):
        self.setup_follow()
        with app.test_request_context(f'/users/stop-following/999999'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post(f'/users/stop-following/999999', follow_redirects=True)

                self.assertEqual(resp.status_code, 404)
                
    def test_user_profile_unauthorized(self):
        with app.test_request_context('/users/profile'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.get('/users/profile')

                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)
                
    def test_get_update_user_profile_form(self):
        with app.test_request_context('/users/profile'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.get('/users/profile')

                self.assertEqual(resp.status_code, 200)
                self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', str(resp.data))
                self.assertIn('form method="POST"', str(resp.data))
                self.assertIn('value="testuser"', str(resp.data))

    def test_post_update_user_profile_form(self):
        with app.test_request_context('/users/profile'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post('/users/profile', follow_redirects=True, 
                              data={'username': 'testupdated',
                                    'password': 'testpassword'})
                                    
                self.assertEqual(resp.status_code, 200)
                self.assertIn('@testupdated', str(resp.data))
    
    def test_update_user_profile_wrong_pw(self):
        with app.test_request_context('/users/profile'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post('/users/profile', follow_redirects=True, 
                              data={'username': 'testupdated',
                                    'password': 'wrongpassword'})

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Password Incorrect', flashed_msgs)

    def test_delete_user(self):
        with app.test_request_context('/users/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.post('/users/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIsNone(g.user)

    def test_unauthorized_delete_user(self):
        with app.test_request_context('/users/delete'):
            app.preprocess_request()
            with app.test_client() as c:
                
                resp = c.post('/users/delete', follow_redirects=True)

                self.assertEqual(resp.status_code, 200)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)

    def test_get_likes(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/users/{self.test.id}/likes'):
            app.preprocess_request()
            with app.test_client() as c:
                with c.session_transaction() as session:
                    session[CURR_USER_KEY] = self.test.id
                resp = c.get(f'/users/{self.test.id}/likes')

                self.assertEqual(resp.status_code, 200)
                self.assertIn(f'@{self.u1.username}', str(resp.data))
                self.assertIn(self.m1.text, str(resp.data))

    def test_unauthorized_get_likes(self):
        self.setup_likes_msgs()
        with app.test_request_context(f'/users/{self.test.id}/likes'):
            app.preprocess_request()
            with app.test_client() as c:
                resp = c.get(f'/users/{self.test.id}/likes')

                self.assertEqual(resp.status_code, 302)
                flashed_msgs = get_flashed_messages()
                self.assertIn('Access unauthorized.', flashed_msgs)