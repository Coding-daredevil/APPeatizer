from flask import Flask
from app import app 
from app_main.models import User

@app.route('/user/signup', methods=['POST'])
def signup():
    return User().signup()

@app.route('/user/signout')
def signout():
    return User().signout()

@app.route('/user/login', methods=['POST'])
def login():
    return User().login()

@app.route('/user/submit_day', methods=['POST'])
def submit_day():
    return User().submit_day()    