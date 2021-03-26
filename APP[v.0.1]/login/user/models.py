from flask import Flask, jsonify, request, session, redirect
from flask_mongoengine import MongoEngine
import datetime
from passlib.hash import pbkdf2_sha256
from app import db
from app import qb
import uuid



class User:

    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signup(self):
        print(request.form)

        # Create the user object #
        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password')
        }

        # Encrypt the password #
        user['password'] = pbkdf2_sha256.encrypt(user['password'])

        # Check for existing email adresses #
        if db.users.find_one({"email":user['email']}):
            return jsonify({"error": "Email address already in use"}), 400
        if db.users.insert_one(user):
            return self.start_session(user)

        return jsonify({"error": "Signup failed"}), 400

    def signout(self):
        session.clear()
        return redirect('/')
        
    def login(self):
        user = db.users.find_one({
            "email": request.form.get('email')
        })

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            return self.start_session(user)
        
        return jsonify({ "error": "Invalid login credentials" }), 401

    def submit_day(self):
        print(request.form)

        # Create the day#
        day = {
            #"_id": uuid.uuid4().hex,
            "breakfast": request.form.get('breakfast'),
            "brunch": request.form.get('brunch'),
            "lunch": request.form.get('lunch'),
            "snack": request.form.get('snack'),
            "dinner": request.form.get('dinner'),
            "details": request.form.get('details'),
            "date": datetime.datetime.utcnow()              #weekday = x.weekday() to get day in int, #import calendar,  #calendar.day_name[x.weekday()] for text, #x.date() == y.date() for date compare only
        }
        
        # Redirect to user's folder #
        ufid = str(session['user']['email'])
        # Check for existing days #
        if db[ufid].insert_one(day):
            return jsonify("success")
        else:
            return jsonify({"error": "Submit failed"}), 400

    def get_ufid(self):
        ufid = str(session['user']['email'])
        return ufid

    def retrieve_days(self, d1 = datetime.datetime.utcnow(), ufid = "default"):
        # User's folder
        if ufid=="default":                                                             # We have to do this because it cannot accept str(session....) above (throws timeout error). 
            ufid = str(session['user']['email'])
        # retrieve latest Monday #
        #x = datetime.datetime.utcnow().date()
        #z = datetime.datetime.utcnow()
        x = d1.date()                                                                   # Current Monday - by default today (only dd/mm/yy)
        z = d1                                                                          # Current Monday - by default today (full)
        y = x.weekday()                                                                 # Today is y day of the week   
        days = []
        for i in range(y+1):
            days.append(x - datetime.timedelta(days=i))                                 # E.g. appends leftwards from today
        days.reverse() 
        cnt=0 
        for i in range(y,6):
            cnt+=1
            days.append(x + datetime.timedelta(days=cnt))                               # E.g. appends rightwards from today
        weekdays = []                                                                   # We store Objects on weekdays
        days_headings = []                                                              # We store the headings (with their date) on days_headings (tuple)
        for i in range(7):
            start = datetime.datetime(days[i].year, days[i].month, days[i].day, 0, 0)
            end = datetime.datetime(days[i].year, days[i].month, days[i].day, 23, 59)
            if db[ufid].find_one({"date" : {"$gte": start, "$lt": end}}) is None:       # If an Object for the specific day does not exist, we create it
                if y<i:
                    new_date =  z + datetime.timedelta(days=i-y)                                  # if y(today) is lower/leftwards to day[i], then add
                elif y>i: 
                    new_date =  z - datetime.timedelta(days=y-i)                                  # if opposite, subtract
                else:
                    new_date = z                                                                # or set today
                day = {
                    "breakfast": "",
                    "brunch": "",
                    "lunch": "",
                    "snack": "",
                    "dinner": "",
                    "details": "",
                    "date": new_date + datetime.timedelta(seconds=20)
                }
                db[ufid].insert_one(day)                                                    # We add the new day into the DB, with the right date.
            weekdays.append(db[ufid].find_one({"date" : {"$gte": start, "$lt": end}}))
            days_headings = (days[0].strftime("%A %d/%m/%Y"), days[1].strftime("%A %d/%m/%Y"), days[2].strftime("%A %d/%m/%Y"), days[3].strftime("%A %d/%m/%Y"), days[4].strftime("%A %d/%m/%Y"), days[5].strftime("%A %d/%m/%Y"), days[6].strftime("%A %d/%m/%Y"))
        return days, days_headings                                                         # Days have to be returned to work as a query for compatability of code w/ Django (otherwise updating table returns error)

    def add_supervisor(self, prof_email):
        if db["users"].find_one({"email": prof_email}) is None:                                                        # If the given Email DOES NOT exist in the database, then inform the user
            return jsonify({"error": "Email address does not exist in database"}), 400
        else:                                                                                                          # If it does exist, we need to check if it already registered as a supervisor
            if prof_email==str(session['user']['email']):
                return jsonify({"error": "You cannot supervise yourself ;)"}), 400
            else:
                x = db["users"].find_one({"email": str(session['user']['email'])})
                if len(x)==5:
                    array = x['supervisors']
                    cnt=0
                    for i in range(len(array)):
                        if array[i]==prof_email:
                            cnt+=1
                    if cnt==0:
                        db["users"].update_one({"_id": str(session['user']['_id'])}, { "$push": { "supervisors": prof_email } } )
                        return jsonify("success")
                    else:
                        return jsonify({"error": "Email address already registered as a supervisor"}), 400
                else:
                    db["users"].update_one({"_id": str(session['user']['_id'])}, { "$push": { "supervisors": prof_email } } )
                    return jsonify("success")
        
            