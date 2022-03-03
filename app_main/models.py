from flask import Flask, jsonify, make_response, request, session, redirect
from flask_mongoengine import MongoEngine
import datetime
from passlib.hash import pbkdf2_sha256
from app import db
from app import qb
from app import conf
import uuid
import requests
import numpy as np
import requests.exceptions
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences

""" Since Free version of EdamamAPI allows up to 100 queries/day, we tripled the number to have enough queries available during Aug21 (had 2-3 people logging). """
url_rapid = conf['edamam']['url_rapid']
count_git, count_gmail, count_fb = 0, 0, 0
headers_git = { 
    'x-rapidapi-key': conf['edamam']['k1'],
    'x-rapidapi-host': conf['edamam']['h1']
}
headers_gmail = {
     'x-rapidapi-key': conf['edamam']['k2'],
     'x-rapidapi-host': conf['edamam']['h2']
}
headers_fb = {
    'x-rapidapi-key': conf['edamam']['k3'],
    'x-rapidapi-host': conf['edamam']['h3']
}

class User:

    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signup(self):
        """User Register

            Args:
             name: user name
             email: user email
             password: password
            
            Returns:
             Registers the user in the database
        """
        print(request.form)
        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password')
        }
        user['password'] = pbkdf2_sha256.encrypt(user['password'])
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
        """Submit Day

            Args:
             form: The form completed by the user containing day intakes.
            
            Returns:
             This currently unused function would work with create_record to register days in the database from forms. Was dropped after developing
             the interactive dietbook.
        """
        print(request.form)
        day = {
            "breakfast": request.form.get('breakfast'),
            "brunch": request.form.get('brunch'),
            "lunch": request.form.get('lunch'),
            "snack": request.form.get('snack'),
            "dinner": request.form.get('dinner'),
            "details": request.form.get('details'),
            "date": datetime.datetime.utcnow()
        }
        ufid = str(session['user']['email'])
        if db[ufid].insert_one(day):
            return jsonify("success")
        else:
            return jsonify({"error": "Submit failed"}), 400

    def get_ufid(self):
        ufid = str(session['user']['email'])
        return ufid

    def retrieve_days(self, d1 = datetime.datetime.utcnow(), ufid = "default"):
        """Retrieve Days

            Args:
             d1: the date of day in question. If not specified, then today.
             ufid: the email/collection_id. If not specified, then the email of the logged in user.
            
            Returns:
             The main function when it comes to dealing with the Dietbook, this retrieves the required days and returns them so they can be rendered
        """
        # User's folder
        if ufid=="default":                                                             # We have to do this because it cannot accept str(session....) above (throws timeout error). 
            ufid = str(session['user']['email'])
        # retrieve latest Monday #
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
        """Register Supervisor

            Args:
             prof_email: email of the proffesional that the user registered in the form.
            
            Returns:
             Either registers the user as part of the patient group of said professional, or return appropriate error.
        """
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
        """Set-up Day

            Args:
             day: the day in question
            
            Returns:
             Upon pressing the 'Expand Day' for the first time, the system initializes all inputs (and creates an empty record in database).
        """
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

    def calculate_mean_calorie_intake(mail):
        """Harris-Benedict formula for Mean Calorie Calculation

            Args:
             mail: the mail of the user in question
            
            Returns:
             Upon collecting the user's personal info, it returns 70% of their bmr, indicating their mean calories required to lose weight.
        """
        #Harris-Benedict formula#
        for res in db['user_info'].find({'email': mail}):
            pi = res['personal_info']
        if pi['sex'] == 'Male':
            bmr = 66.47 + (13.75 * float(pi['weight'])) + (5.003 * float(pi['height'])) - (6.755 * int(pi['age']))
        else:
            bmr = 655.1 + (9.563 * float(pi['weight'])) + (1.850 * float(pi['height'])) - (4.676 * int(pi['age']))
        return round(bmr*0.7)

    def check_query_validity(self, book):
        """Query Validity

            Args:
             book: the group (book) of days in question. This number depends on whether we are dealing in day/week prediction, 
                as well as how many days were selected upon training of the model.
            
            Returns:
             1 if the query is deemed valid, 0 if invalid.
        """
        num_days = len(book)
        bad_days = 0
        for day in book:
            if day['breakfast'] == [] and day['brunch'] == [] and day['lunch'] == [] and day['lunch'] == [] and day['dinner'] == []:
                bad_days += 1
        return 1 if 100*(bad_days/num_days) < 25 else 0


    def create_model_input_from(self, dct, col, book, maxseq):
        """Create Model Input

            Args:
             dct: the matching matrix that matches user emails to id tokens.
             col: the email in question to retrieve the correct user information.
             book: the group of days meant to be used for the ML prediction.
             maxseq: the maximum array sequence (from padding) which was defined in the process of feature engineering and selection.
            
            Returns:
             Transforms the raw text retrieved by the site/database to a proper input for the model and returns the model's input (not result).
        """
        def find_deficit_percentage(col, total_day_cals):
            #Harris-Benedict formula#
            for uinfo in db['user_info'].find({'email': col}):
                pi = uinfo['personal_info']
            if pi['sex'] == 'Male':
                bmr = 66.47 + (13.75 * float(pi['weight'])) + (5.003 * float(pi['height'])) - (6.755 * int(pi['age']))
            else:
                bmr = 655.1 + (9.563 * float(pi['weight'])) + (1.850 * float(pi['height'])) - (4.676 * int(pi['age']))
            goal = round(bmr*0.7)
            deficit = goal - total_day_cals
            return round(100*deficit/goal,3)
        num_days = len(book)
        eating_periods = ['breakfast', 'brunch', 'lunch', 'snack', 'dinner']
        sequence_name = sequence_cals = sequence_carb = sequence_fat = sequence_prot = sequence_sod = sequence_sug = sequence_scr = ""
        for res in book:
            if any(res[consumption]!=[] for consumption in eating_periods):          ### If there has been any eating, then proceed
                total_day_cals = 0
                intersection = [x for x in eating_periods if res[x]!=[]]
                for eating_period in intersection:
                    for log in res[eating_period]:
                        sequence_name += res[eating_period][log]['name']+' ||| '
                        sequence_cals += str(round(res[eating_period][log]['ENERC_KCAL']['quantity'])) + ' '
                        total_day_cals += round(res[eating_period][log]['ENERC_KCAL']['quantity'])
                        sequence_carb += str(round(res[eating_period][log]['CHOCDF']['quantity'])) + ' '
                        sequence_fat += str(round(res[eating_period][log]['FAT']['quantity'])) + ' '
                        sequence_prot += str(round(res[eating_period][log]['PROCNT']['quantity'])) + ' '
                        sequence_sod += str(round(res[eating_period][log]['NA']['quantity'])) + ' '
                        sequence_sug += str(round(res[eating_period][log]['SUGAR']['quantity'])) + ' ' if 'SUGAR' in res[eating_period][log].keys() else '0 '
                sequence_scr += str(find_deficit_percentage(col, total_day_cals)) + ' '
            else:
                sequence_scr += str(find_deficit_percentage(col, 0)) + ' '
        inpt = {
            'USER_ID': dct[col],
            'sequence_name': sequence_name[:-5],
            'sequence_cals': sequence_cals.rstrip(),
            'sequence_carb': sequence_carb.rstrip(),
            'sequence_fat': sequence_fat.rstrip(),
            'sequence_prot': sequence_prot.rstrip(),
            'sequence_sod': sequence_sod.rstrip(),
            'sequence_sug': sequence_sug.rstrip(),
            'sequence_scr': sequence_scr.rstrip()
        }
        ###
        arr_cals = [np.array(inpt['sequence_cals'].split(' ')).astype(float)]
        arr_carb = [np.array(inpt['sequence_carb'].split(' ')).astype(float)]
        arr_fat =  [np.array(inpt['sequence_fat'].split(' ')).astype(float)]
        arr_prot = [np.array(inpt['sequence_prot'].split(' ')).astype(float)]
        arr_sod =  [np.array(inpt['sequence_sod'].split(' ')).astype(float)]
        arr_sug =  [np.array(inpt['sequence_sug'].split(' ')).astype(float)]
        arr_scr =  [np.array(inpt['sequence_scr'].split(' ')).astype(float)]
        arr_cals = pad_sequences(arr_cals, maxlen=maxseq, dtype=float, value=0)
        arr_carb = pad_sequences(arr_carb, maxlen=maxseq, dtype=float, value=0)
        arr_fat  = pad_sequences(arr_fat, maxlen=maxseq, dtype=float, value=0)
        arr_prot = pad_sequences(arr_prot, maxlen=maxseq, dtype=float, value=0)
        arr_sod  = pad_sequences(arr_sod, maxlen=maxseq, dtype=float, value=0)
        arr_sug  = pad_sequences(arr_sug, maxlen=maxseq, dtype=float, value=0)
        inpt = {
            'USER_ID': tf.constant([inpt['USER_ID']]),
            'CALS': tf.constant(arr_cals),
            'CARB': tf.constant(arr_carb),
            'FAT': tf.constant(arr_fat),
            'PROT': tf.constant(arr_prot),
            'SOD': tf.constant(arr_sod),
            'SUG': tf.constant(arr_sug),
            'SCR': tf.constant(arr_scr),
        }
        return inpt

    def calculate_summary(self, day):
        """Calculate Summary

            Args:
             day: the day in question
            
            Returns:
             Calculates the total amount of calories, proteins, etc and returns them to be printed in the 'Expanded Day' Dietbook View (the one colored in the bottom).
        """
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
        """Make Edamam Query

            Args:
             query_txt: the query text registered by the user in the form
            
            Returns:
             The calorie result of EdamamAPI on the said query.
        """
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
        """Dietbook Input to Nutrition

            Args:
             user_input: a list containing the words seperated by '+'
            
            Returns:
             Makes the Query in Edamam (by using the 3 API keys in-turn) and if a result is found (not calories=0 and weight=0), returns it in proper form (list of dicts).
        """
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
        """Exercise Value to Calories

            Args:
             value: String of Exercise Type
            
            Returns:
             Returns calorie burnout depending on exercise type. Basic version. When expanded it should return based on BMR.
        """
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
        """Exercise Value to Calories

            Args:
             user_mail: User Email
            
            Returns:
             Returns personal information of user by utilizing their user email.
        """
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