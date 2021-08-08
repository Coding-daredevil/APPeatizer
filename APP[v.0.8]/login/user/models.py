from flask import Flask, jsonify, make_response, request, session, redirect
from flask_mongoengine import MongoEngine
import datetime
from passlib.hash import pbkdf2_sha256
from app import db
from app import qb
import uuid
import requests
import requests.exceptions

url_rapid = "https://edamam-edamam-nutrition-analysis.p.rapidapi.com/api/nutrition-data"
count_git = 0
count_gmail = 0
count_fb = 0
headers_git = {
    'x-rapidapi-key': "54992b39a4mshbc5672c41c536f1p183777jsn96830647d8b8",
    'x-rapidapi-host': "edamam-edamam-nutrition-analysis.p.rapidapi.com"
}
headers_gmail = {
     'x-rapidapi-key': 'deacfc0616msh83f86c85a26a646p1985c5jsnbc9f56f99556',
     'x-rapidapi-host': 'edamam-edamam-nutrition-analysis.p.rapidapi.com'
}
headers_fb = {
    'x-rapidapi-key': "d1d8c92896msh1c5f8eb70d89c72p19c375jsn38d73f8b2cd6",
    'x-rapidapi-host': "edamam-edamam-nutrition-analysis.p.rapidapi.com"
}

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

    def day_setup(self, day):
        key = day[0].id
        if len(day[0].exercise_status) == 0:
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'breakfast' : 'False' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'breakfast_burnout' : '0' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'brunch' : 'False' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'brunch_burnout' : '0' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'lunch' : 'False' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'lunch_burnout' : '0' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'snack' : 'False' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'snack_burnout' : '0' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'dinner' : 'False' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'exercise_status.'+'dinner_burnout' : '0' } } )
            print("CHECK")
        if len(day[0].miscellaneous) == 0:
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_hunger_before' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_hunger_before' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_hunger_before' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_hunger_before' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_hunger_before' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_hunger_after' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_hunger_after' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_hunger_after' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_hunger_after' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_hunger_after' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_mood' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_mood' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_mood' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_mood' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_mood' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_company' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_company' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_company' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_company' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_company' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_filled' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_filled' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_filled' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_filled' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_filled' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'breakfast_weight_measurement' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'brunch_weight_measurement' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'lunch_weight_measurement' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'snack_weight_measurement' : 'Unset' } } )
            db[User().get_ufid()].update_one({"_id": key}, { "$set": { 'miscellaneous.'+'dinner_weight_measurement' : 'Unset' } } )
        return jsonify("success")

    def calculate_summary(self, day):
        key = day[0].id
        checklist = ['breakfast', 'brunch', 'lunch', 'snack', 'dinner']
        total_calories, total_protein, total_carbs, total_fat, times_exercised, calories_burnt = 0, 0, 0, 0, 0, 0
        for period in checklist:
            if len(day[0][period]) != 0:
                for iid in day[0][period]:
                    total_calories += day[0][period][iid]['ENERC_KCAL']['quantity']
                    total_protein += day[0][period][iid]['PROCNT']['quantity']
                    total_carbs += day[0][period][iid]['CHOCDF']['quantity']
                    total_fat += day[0][period][iid]['FAT']['quantity']
            if day[0].exercise_status[period] == 'True':
                times_exercised += 1
                calories_burnt += int(day[0].exercise_status[period+'_burnout'])
        return {'total_calories': total_calories, 'total_protein': total_protein, 'total_carbs': total_carbs, 'total_fat': total_fat,'times_exercised': times_exercised, 'calories_burnt': calories_burnt}

    def make_edamam_query(self, query_txt):
        querystring = {"ingr":query_txt}
        global count_git, count_gmail, count_fb
        try:
            tpl = (count_git, count_gmail, count_fb)
            idx = tpl.index(min(tpl))
            if idx==0:
                response = requests.request("GET", url_rapid, headers=headers_git, params=querystring)
                count_git += 1
                print('Count_GIT is:', count_git)
            elif idx==1:
                response = requests.request("GET", url_rapid, headers=headers_gmail, params=querystring)
                count_gmail += 1
                print('Count_GMAIL is:', count_gmail)
            else:
                response = requests.request("GET", url_rapid, headers=headers_fb, params=querystring)
                count_fb += 1
                print('Count_FB is:', count_fb)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return jsonify({"error": "Down"}), 400
        except requests.exceptions.HTTPError:
            return jsonify({"error": "4xx or 5xx fatal error"}), 400
        else:
            response = response.json()
            if response['calories'] == 0 and response['totalWeight'] == 0:
                return jsonify({"error": "Wrong Input Given"}), 400
            else:
                print("CALORIES ARE: ", response['calories'])
                return jsonify({"error": "Calories: "+str(response['calories'])}), 400

    def dietbook_input_to_nutrition(self, user_input):
        words = user_input.split('+')                                                           # We split the words
        global count_git, count_gmail, count_fb
        dict_list = []
        for row in words:
            try:
                tpl = (count_git, count_gmail, count_fb)
                idx = tpl.index(min(tpl))
                if idx==0:
                    response = requests.request("GET", url_rapid, headers=headers_git, params={'ingr': row})
                    count_git += 1
                elif idx==1:
                    response = requests.request("GET", url_rapid, headers=headers_gmail, params={'ingr': row})
                    count_gmail += 1
                else:
                    response = requests.request("GET", url_rapid, headers=headers_fb, params={'ingr': row})
                    count_fb += 1
                response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return jsonify({"error": "Down"}), 400
            except requests.exceptions.HTTPError:
                return jsonify({"error": "4xx or 5xx fatal error"}), 400
            else:
                response = response.json()
                if response['calories'] == 0 and response['totalWeight'] == 0.0:
                    dict_list = []
                    return dict_list
                else:
                    temp_dict = {'name': row.rstrip()}
                    temp_dict.update(response["totalNutrients"])
                    dict_list.append(temp_dict)
        return dict_list

    def exercise_status_to_calories(self, value):
        if value == 'Very Light Exercise':
            value = int(100)
        elif value == 'Light Exercise':
            value = int(150)
        elif value == 'Moderate Exercise':
            value = int(200)
        elif value == 'Intense Exercise':
            value = int(250)
        elif value == 'Very Intense Exercise':
            value = int(300)
        else:
            value = int(-1)
        return value

    def retrieve_personal_info(self, user_mail):
        user_name = db.users.find_one({"email":user_mail})['name']
        if db.user_info.find_one({"name":user_name}) is None:
            personal_info = { 
                'name': user_name,
                'email': user_mail,
                'personal_info': {
                    'sex': 'Unset',
                    'age': 'Unset',
                    'height': 'Unset',
                    'weight': 'Unset',
                }
            }
            db.user_info.insert_one(personal_info)
        else:
            personal_info = db.user_info.find_one({"email":user_mail})['personal_info']
        return personal_info