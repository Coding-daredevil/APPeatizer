from flask import Flask, render_template, session, redirect, request, jsonify, json
from functools import wraps
from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
import pymongo
import datetime, time
import uuid

#print(datetime.now().date())
app = Flask(__name__)
app.secret_key = b'\xb7M\x88^S\x19\x9a\xc4n\x04\xb3\xbd\x06\xf1\xb11'

# MongoDB
client = pymongo.MongoClient('localhost', 27017)
db = client.accounts

## Live Book Update ##
app.config['MONGODB_SETTINGS'] = {
    'db': 'accounts',
    'host': 'localhost',
    'port': 27017
}
qb = db
#ufid = User().get_ufid()
qb = MongoEngine()
qb.init_app(app)

# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return wrap


#Routes
from user import routes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard/')
@login_required

def dashboard():
    return render_template('dashboard.html')

from user.models import User 

@app.route('/dietbook/')
@login_required
def dietbook():
    return render_template('dietbook.html')

###[Automatically Loads User's DietBook based on Today]###
@app.route('/dietbook_automatic_load', methods = ['GET','POST'])
@login_required
def dietbook_automatic_load():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    days, headings = User().retrieve_days()
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col="default")

###[Specifically Loads User's Dietbook based on Selected Date]###
@app.route('/dietbook_specific_load', methods = ['GET','POST'])
@login_required
def dietbook_specific_load():
    col = str(request.form['col'])
    if col=="default":
        col = User().get_ufid()
    date_get = str(request.form.get('date_get'))
    if date_get == 'None':
        date_get = str(request.form['date'])
    d1 = datetime.datetime.strptime(date_get,"%Y-%m-%d")
    #date_get = time.mktime(datetime.datetime.strptime(date_get,"%Y-%m-%d").timetuple())
    class Book(qb.Document):
        meta = {
            'collection': col
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    days, headings = User().retrieve_days(d1, col)
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)

###[Update DietBook's Inputs]###
@app.route('/updatebook', methods=['POST'])
def updatebook():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    pk = str(request.form.get('pk'))
    pk = pk.split('+')
    type_of_update = pk[3]
    namepost = pk[4]
    value = str(request.form.get('value'))
    day_rs = Book.objects(id=pk[0]).first()
    if not day_rs:
        return json.dumps({'error':'data not found'})
    else:
        if type_of_update == 'food_update':
            if value == 'del':
                db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$unset": { namepost+'.'+pk[1]: 1 } } )
                #db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$pull": { namepost: null } } )
            else:
                dict_list = User().dietbook_input_to_nutrition(value)
                if len(dict_list) == 0:
                    return jsonify("Wrong Input Given"), 400
                if pk[1] == 'new':
                    pk[1] = str(len(day_rs[namepost]))
                db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$set": { namepost+'.'+pk[1] : dict_list[0] } } )
        elif type_of_update == 'exercise':
            pk.append('day')
            if value == 'False':
                value = 'True'
            elif value == 'True':
                value = 'False'
            db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$set": { 'exercise_status.'+namepost : value } } ) 
        elif type_of_update == 'exercise_burnout':
            pk.append('day')
            if not value.isnumeric():
                value = User().exercise_status_to_calories(value)
                if value == -1:
                    return jsonify("Wrong Input Given"), 400
            db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$set": { 'exercise_status.'+namepost : value } } )
        elif type_of_update == 'misc':
            pk.append('day')
            db[User().get_ufid()].update_one({"_id": ObjectId(pk[0])}, { "$set": { 'miscellaneous.'+namepost : value } } )  
        if pk[5] == 'normal':
                dt = datetime.datetime.fromtimestamp(int(pk[2])/1000)
                days, headings = User().retrieve_days(dt)
                start_date = days[0]
                end_date = days[6] + datetime.timedelta(days=1)
                book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
                start_date_js = int(time.mktime(start_date.timetuple())) * 1000
                end_date_js = int(time.mktime(end_date.timetuple())) * 1000
                return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=User().get_ufid())   
        elif pk[5] == 'day':
            date = pk[2]
            start_date = date[:10] + ' 00:00:00.000000'
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
            end_date  = date[:10] + ' 23:59:59.999999'
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S.%f')
            headings = [(start_date.strftime("%A %d/%m/%Y"))]
            book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
            start_date_js = int(time.mktime(start_date.timetuple())) * 1000
            end_date_js = int(time.mktime(end_date.timetuple())) * 1000
            summary = User().calculate_summary(book)
            return render_template('dietbook_day.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=User().get_ufid(), summary=summary)  
        else:
            return json.dumps({'status':'OK'})
          

@app.route('/add', methods=['GET', 'POST'])
def create_record():
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    txtbreakfast = request.form['txtbreakfast']
    txtbrunch = request.form['txtbrunch']
    txtlunch = request.form['txtlunch']
    txtsnack = request.form['txtsnack']
    txtdinner = request.form['txtdinner']
    txtdetails = request.form['txtdetails']
    daysave = Book(breakfast=txtbreakfast, brunch=txtbrunch, lunch=txtlunch, snack=txtsnack, dinner=txtdinner, details=txtdetails, date=datetime.datetime.utcnow())
    daysave.save()
    return redirect('/dietbook/')

@app.route('/delete/<string:getid>', methods = ['POST','GET'])
def delete_book(getid):
    class Book(qb.Document):
        meta = {
            'collection': User().get_ufid()
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    print(getid)
    days = Book.objects(id=getid).first()
    if not days:
        return jsonify({'error': 'data not found'})
    else:
        days.delete()
    return redirect('/')

@app.route('/updateweek', methods=['POST','GET'])
def updateweek():
    col = str(request.form['col'])
    if col=="default":
        col = User().get_ufid()
    class Book(qb.Document):
        meta = {
            'collection': col
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    type_of_request = int(request.form['type_of_request'])
    if not type_of_request:
        timestamp = int(request.form['timestamp'])
        dt_new = datetime.datetime.fromtimestamp(timestamp)
        days, headings = User().retrieve_days(dt_new,col)
        start_date = days[0]
        end_date = days[6] + datetime.timedelta(days=1)
        book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
        start_date_js = int(time.mktime(start_date.timetuple())) * 1000
        end_date_js = int(time.mktime(end_date.timetuple())) * 1000
        return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)
    else:
        date = str(request.form['date'])
        start_date = date[:10] + ' 00:00:00.000000'
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
        end_date  = date[:10] + ' 23:59:59.999999'
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S.%f')
        headings = [(start_date.strftime("%A %d/%m/%Y"))]
        book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
        User().day_setup(book)
        start_date_js = int(time.mktime(start_date.timetuple())) * 1000
        end_date_js = int(time.mktime(end_date.timetuple())) * 1000
        summary = User().calculate_summary(book)
        return render_template('dietbook_day.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col, summary=summary)
    

@app.route('/dietbook_control/')
@login_required
def dietbook_control():
    class dbUser(qb.Document):
        meta = {
            'collection': "users"
        }
        name = qb.StringField()
        email = qb.StringField()
        password = qb.StringField()
        supervisors = qb.ListField()
    userlist = dbUser.objects.filter(supervisors__contains=User().get_ufid())           # Returns ALL users that include session's users email in their supervisor's list.
    return render_template('dietbook_control.html', userlist=userlist)

@app.route('/dietbook_uselect', methods=['POST','GET'])
@login_required
def dietbook_uselect():
    username = request.form.get('user')
    x = db.users.find_one({"name":username})
    col = str(x['email'])
    class Book(qb.Document):
        meta = {
            'collection': col
        }
        breakfast = qb.ListField()
        brunch = qb.ListField()
        lunch = qb.ListField()
        snack = qb.ListField()
        dinner = qb.ListField()
        details = qb.ListField()
        exercise_status = qb.ListField()
        date = qb.DateTimeField()
        miscellaneous = qb.ListField()
    d1 = datetime.datetime.utcnow()
    ufid = col
    days, headings = User().retrieve_days(d1,ufid)
    start_date = days[0]
    end_date = days[6] + datetime.timedelta(days=1)
    book = Book.objects.filter(date__lte=end_date, date__gte=start_date).order_by('date')
    start_date_js = int(time.mktime(start_date.timetuple())) * 1000
    end_date_js = int(time.mktime(end_date.timetuple())) * 1000
    return render_template('dietbook_table.html', headings=headings, data=book, start_date=start_date_js, end_date=end_date_js, col=col)

@app.route('/update_info', methods=['GET', 'POST'])
def update_info():
    class dbUser_info(qb.Document):
        meta = {
            'collection': "user_info"
        }
        name = qb.StringField()
        email = qb.StringField()
        personal_info = qb.ListField()
    user_mail = User().get_ufid()
    personal_info = {
        'sex': request.form.get('sex'),
        'age': request.form.get('age'),
        'height': request.form.get('height'),
        'weight': request.form.get('weight'),
    }
    db['user_info'].update_one({"email": user_mail}, { "$set": { 'personal_info' : personal_info } } )
    return render_template('personal_info.html', personal_info = personal_info)

@app.route('/req_prof_form/')
@login_required
def req_prof_form():
    return render_template('req_prof_form.html')

@app.route('/addprof', methods=['POST','GET'])
@login_required
def addprof():
    prof_email = request.form.get('email')
    return User().add_supervisor(prof_email)

@app.route('/edamam_api/')
@login_required
def edamam_api():
    return render_template('edamam_api.html')

@app.route('/edamam_rquery', methods=['POST','GET'])
@login_required
def edamam_rquery():
    query = request.form.get('query_string')
    return User().make_edamam_query(query)

@app.route('/personal_info/')
@login_required
def personal_info():
    personal_info = User().retrieve_personal_info(User().get_ufid())
    return render_template('personal_info.html', personal_info = personal_info)