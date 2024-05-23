from app import app, CURR_USER_KEY
import os
from flask import session
from unittest import TestCase
from models import db, connect_db, User, PokemonTeam

"""
url set to test db, not standard one. CSRF disabled because
it makes testing difficult.
"""
os.environ['DATABASE_URL'] = 'postgresql:///pokeapi_test'
db.create_all()
app.config['WTF_CSRF_ENABLED'] = False

class UserAuth(TestCase):
    """Tests signup, login, and logout routes"""

    def setUp(self):
        """create a test user, which will be done for all testing classes"""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", password="testpassword")
        self.testuser_id = 123
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_signup_get(self):
        with self.client as client:
            resp = client.get("/signup")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sign Up!", resp.get_data(as_text=True))

    def test_signup_post(self):
        with self.client as client:
            resp = client.post("/signup", data={
                "username" : "testuser2",
                "password" : "password123"
            })

            # 302 and not 200 because the route redirects on success
            self.assertEqual(resp.status_code, 302)
            user = User.query.filter_by(username="testuser2").first()
            self.assertTrue(user)

    def test_login_logout(self):
        with self.client as client:
            loginResp = client.post("/login", data={
                "username" : "testuser",
                "password" : "testpassword"
            })

            self.assertEqual(loginResp.status_code, 302)

            logoutResp = client.get("/logout")

            self.assertEqual(logoutResp.status_code, 302)

class UserProfile(TestCase):
    """Test the routes related to the user profile"""

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", password="testpassword")
        self.testuser_id = 123
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_profile(self):
        """visit the user profile while logged in"""
        with self.client as client:
            # Set the session to our testuser's id to mimic being signed in
            with client.session_transaction() as change_session:
                change_session['current_user'] = 123

            resp = client.get(f"/user/{self.testuser_id}", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("'s Profile", resp.get_data(as_text=True))

    def test_change_password(self):
        """change the password and log in again using new password"""
        with self.client as client:
            with client.session_transaction() as change_session:
                change_session['current_user'] = 123

        resp = client.post(f"/user/{self.testuser_id}/changepassword", data={
            "oldPassword" : "testpassword",
            "newPassword1" : "admin123",
            "newPassword2" : "admin123"
        })

        self.assertEqual(resp.status_code, 302)
        user = User.query.filter_by(username="testuser").first()
        self.assertTrue(user)
        
        loginResp = client.post("/login", data={
                "username" : "testuser",
                "password" : "admin123"
            })
        self.assertEqual(loginResp.status_code, 302)

    def test_delete_user(self):
        """delete user and check if user has been deleted from db"""
        with self.client as client:
            with client.session_transaction() as change_session:
                change_session['current_user'] = 123
        
        resp = client.get(f"/user/{self.testuser_id}/delete")

        self.assertEqual(resp.status_code, 302)
        user = User.query.filter_by(username="testuser").first()
        self.assertFalse(user)

class Pokemon(TestCase):
    """Tests routes related to pokemon team creation and deletion"""

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", password="testpassword")
        self.testuser_id = 123
        self.testuser.id = self.testuser_id

        db.session.commit()

        with self.client as client:
            with client.session_transaction() as change_session:
                change_session['current_user'] = 123

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_pokemon_team(self):
        """access team creation page"""
        with self.client as client:
            resp = client.get("/teams/new")
            
            self.assertEqual(resp.status_code, 200)

    def test_deletion(self):
        """Create team and check db to see if it deleted"""
        with self.client as client:
            testArr = [["wooper", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/194.png"],
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""],
            ["", ""]]

            newTeam = PokemonTeam(
                pokemon1 = str(testArr[0][0]),
                pokemon1URL = str(testArr[0][1]),
                pokemon2 = str(testArr[1][0]),
                pokemon2URL = str(testArr[1][1]),
                pokemon3 = str(testArr[2][0]),
                pokemon3URL = str(testArr[2][1]),
                pokemon4 = str(testArr[3][0]),
                pokemon4URL = str(testArr[3][1]),
                pokemon5 = str(testArr[4][0]),
                pokemon5URL = str(testArr[4][1]),
                pokemon6 = str(testArr[5][0]),
                pokemon6URL = str(testArr[5][1]),
                user_id = self.testuser_id
            )

            db.session.add(newTeam)
            db.session.commit()

            team = PokemonTeam.query.filter_by(user_id=123).first()
            self.assertTrue(team)

            resp = client.get("/teams/1/delete")
            self.assertEqual(resp.status_code, 302)

            team = PokemonTeam.query.filter_by(user_id=123).first()
            self.assertFalse(team)