import json
from flask import Flask, flash, jsonify, render_template, request, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from models import User, PokemonTeam, connect_db, db
from forms import * 

app = Flask(__name__)

"""
URI is currently set to a LOCAL psql db and must be changed to 
the internal URI when deployed on Render. To run locally, use
flask run and for deployment, use flask run --host=0.0.0.0.
Change to ..._test when testing with test_app.py
"""
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pokeapi'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pokeapi_test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://pokeapi_db_thls_user:Tv2NwxTdgzAd7FK7w7lqZyN20nsO3KI6@dpg-cots20n109ks73d49nkg-a/pokeapi_db_thls'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = "somekey"
toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

CURR_USER_KEY = "current_user"



"""
Global user route/functions

Uses the session to help manage which user is currently logged in.
Required for routes that need to check if the right user is logged
in before displaying private information. 
"""

@app.before_request
def add_user_to_g():
    """
    Runs before every route request. Sets the global user based on
    whether or not the session contains a user.
    """

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def log_user_in(user):
    """
    Parameters
    ----------
    user : User object

    stores a user's id in the session
    """
    session[CURR_USER_KEY] = user.id

def log_user_out():
    """
    removes the user session
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


"""
Registration and Authentication Routes

Allows the user to signup, login, and logout of their account
"""

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    method = GET
    ------------
    if the route is requested with GET, generate a NewUserForm()
    from forms.py which asks for username and password. Then
    renders an html template with this new user form.

    method = POST
    -------------
    uses flaskwtf's built in validation to prevent CSRFs. If
    valid, runs User.signup which is defined in the User model.
    """

    form = NewUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.signup(username, password)

        # If username is already taken, flash message and return to form
        try:
            db.session.commit()
        except exc.SQLAlchemyError:
            flash("Username already registered")
            return redirect("/signup")

        # adds user to session
        log_user_in(user)
        return redirect("/")

    return render_template("/users/signup.html", form=form, user=g.user)

@app.route("/logout")
def logout():
    """removes current user"""
    if g.user:
        log_user_out()
        flash(f"Logged out user {g.user.username}")
        return redirect("/")
    
    else:
        flash("No user logged in")
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """logs the user in"""

    form = LogUserIn()

    if form.validate_on_submit():
        user = User.authenticateUser(form.username.data, form.password.data)

        if user:
            log_user_in(user)
        else:
            flash("Incorrect credentials")
        return redirect("/login")

    else:
        return render_template("/users/login.html", form=form, user=g.user)


"""
User Profile Routes

Allows user to view account, change their password, or delete account.
All routes require the correct user to be signed in.
"""

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    """
    Parameters
    ----------
    user_id : int

    renders the profile template with the logged in user's information
    which includes options to change password, delete account, and
    their created pokemon teams.
    """

    if not g.user:
        flash("Must be signed in to access")
        return redirect("/")
    
    # get list of all teams from db with user_id
    # iterate through teams
    # iterate through pokemon in teams
    # use jinja to setup name + sprite
    allTeams = PokemonTeam.query.filter(PokemonTeam.user_id==user_id).all()
    teamsArr = []
    numTeams = len(allTeams)
    i = 0
    while (i < numTeams):
        teamsArr.append([])
        teamsArr[i].append(allTeams[i].pokemon1)
        teamsArr[i].append(allTeams[i].pokemon1URL)
        teamsArr[i].append(allTeams[i].pokemon2)
        teamsArr[i].append(allTeams[i].pokemon2URL)
        teamsArr[i].append(allTeams[i].pokemon3)
        teamsArr[i].append(allTeams[i].pokemon3URL)
        teamsArr[i].append(allTeams[i].pokemon4)
        teamsArr[i].append(allTeams[i].pokemon4URL)
        teamsArr[i].append(allTeams[i].pokemon5)
        teamsArr[i].append(allTeams[i].pokemon5URL)
        teamsArr[i].append(allTeams[i].pokemon6)
        teamsArr[i].append(allTeams[i].pokemon6URL)
        teamsArr[i].append(allTeams[i].id)
        i += 1

    return render_template("/users/profile.html", user=g.user, teams=teamsArr)

@app.route("/user/<int:user_id>/changepassword", methods=["GET", "POST"])
def change_password(user_id):
    """
    parameters
    ----------
    user_id : int

    method = GET
    ------------
    first checks to see if the right user is logged in. Creates a password form
    which asks for the old password and the new password twice. Renders a
    template with form.

    method = POST
    -------------
    again, uses flaskwtf's built in validation. Checks that the old password is
    correct and that the new passwords match before commiting changes to db.
    """

    if not g.user:
        flash("Must be logged in ")
        return redirect("/")
    if g.user.id != user_id:
        flash("Must be logged in ")
        return redirect("/")
    
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if (not User.authenticateUser(g.user.username, form.oldPassword.data)):
            flash("Old password is incorrect")
            return redirect(f"/user/{user_id}/changepassword")
        if (not form.newPassword1.data == form.newPassword2.data):
            flash("New passwords must match")
            return redirect(f"/user/{user_id}/changepassword")
        
        User.changePassword(g.user.id, form.newPassword1.data)
        print("password changed")

        return redirect(f"/user/{user_id}")
    
    return render_template("/users/changepassword.html", form=form, user=g.user)

@app.route("/user/<int:user_id>/delete")
def delete_user(user_id):
    """deletes a user"""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect("/")

"""
Homepage

Shows only the navbar and the option to create a new team
"""

@app.route("/")
def temp_homepage():
    """Homepage with signin options"""
    return render_template("homepage.html", user=g.user)

"""
Team Routes

Routes for the creation and deletion of Pokemon teams
"""

@app.route("/teams/new", methods=["GET", "POST"])
def create_new_team():
    """
    method = GET
    ------------
    Checks if the user is logged in before presenting form
    to search Pokemon and add them

    method = POST
    -------------
    Separates pokemon names and their sprite urls before
    adding them to the db
    """
    
    if not g.user:
        flash("Must be logged in")
        return redirect("/")

    if request.method == "POST":
        response = request.get_json()
        newTeam = PokemonTeam(
            pokemon1 = str(response[0][0]),
            pokemon1URL = str(response[0][1]),
            pokemon2 = str(response[1][0]),
            pokemon2URL = str(response[1][1]),
            pokemon3 = str(response[2][0]),
            pokemon3URL = str(response[2][1]),
            pokemon4 = str(response[3][0]),
            pokemon4URL = str(response[3][1]),
            pokemon5 = str(response[4][0]),
            pokemon5URL = str(response[4][1]),
            pokemon6 = str(response[5][0]),
            pokemon6URL = str(response[5][1]),
            user_id = g.user.id
        )
        db.session.add(newTeam)
        db.session.commit()

    return render_template("/teams/create-team.html", user=g.user)

@app.route("/teams/<int:team_id>/delete")
def delete_team(team_id):
    """
    parameters
    ----------
    team_id : int

    finds a Pokemon team by their id and deletes it from db
    """
    team = PokemonTeam.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    return redirect(f"/user/{g.user.id}")