######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64
import logging

logging.basicConfig(level=logging.DEBUG)

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'potatoes'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'david' # david for me, but usually change this to "root"
app.config['MYSQL_DATABASE_PASSWORD'] = '' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from User") 
users = cursor.fetchall()

def getUserList():
	cursor.execute("SELECT email from User") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM User WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	#check if email is registered
	if cursor.execute("SELECT user_id, password FROM User WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		user_id = str(data[0][0] )
		pwd = str(data[0][1] )

		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('profile', uid=user_id)) #profile is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('message.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('improved_register.html', supress='True')  

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		print(email)
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	test = isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO User (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('message.html', message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

#end photo uploading code 
def execute_query(query):
	cursor.execute(query)
	conn.commit()

#defines a function for extracting the data from a query
def extractData(query):
	cursor.execute(query)
	logging.debug("Query {0} executed".format(query))
	data = cursor.fetchall() # fetches all rows of the query
	return data



def getUserIdFromEmail(email):
	return_id = -1
	try: #tries the query
		cursor.execute("SELECT user_id FROM User WHERE email = '{0}'".format(email))
		return_id = cursor.fetchone()[0]
	except Exception as e:
		logging.debug("Get user id exception!")
		return -1
	return return_id

def getEmailFromUserID(uid):
	return_email = -1
	try: #tries the query
		cursor.execute("SELECT email FROM User WHERE user_id = '{0}'".format(uid))
		return_email = cursor.fetchone()[0]
	except Exception as e:
		logging.debug("Get email exception!")
		return -1
	return return_email

def isEmailUnique(email):
	#use this to check if a email has already been registered
	if cursor.execute("SELECT email FROM User WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

# code for users and friends begins
def getUsersPhotos(uid):
	photos = extractData("SELECT imgdata, photo_id, caption FROM Photo WHERE user_id = '{0}'".format(uid))
	return photos #note: list of tuples, [(imgdata, pid), ...]

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/profile/<uid>')
def profile(uid):
	email = getEmailFromUserID(uid)

	if (flask_login.current_user.is_authenticated):
		logged_in_user = flask_login.current_user.id
		user_id = getUserIdFromEmail(logged_in_user)
		logging.debug(logged_in_user)
		return render_template('hello.html', uid=user_id, user=logged_in_user)
	else:
		return render_template('hello.html', user=None)

	return render_template('profile.html', name=email)

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		print(caption)
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor.execute("INSERT INTO Photo (imgdata, user_id, caption) VALUES ('{0}', '{1}', '{2}' )".format(photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid) )
	#The method is GET so we return a HTML form to choose an album to upload the photo.
	else:
		return render_template('upload.html')

@app.route('/friend', methods=['GET', 'POST'])
@flask_login.login_required
def find_users():
	email = flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET': # if request is get (user navigated to the URL)
		# optional: change fname lname to be not null and display those
		data = extractData("SELECT email FROM User WHERE user_id <> {0};".format(uid))
		friends = extractData("SELECT email FROM (SELECT * FROM Friendship WHERE follower_user_id={0}) temp JOIN User ON temp.followed_user_id = User.user_id;".format(uid)) 
		return render_template('friend.html', name=email, friends=friends,data=data)
    
	else: #if request is post (user posted some information)
		message = "Nothing happened! Try again"

		#get the user searched from the 'USER_EMAIL' row of the form
		query_email = request.form['USER_EMAIL']
		query_id = getUserIdFromEmail(query_email)
		if (query_id == -1):
			message = "User {0} not found. Try again".format(query_email)
		elif query_email == email:
			message = "Nice try, you can't add yourself!"
		else:
			query = "INSERT INTO Friendship VALUES({0}, {1});".format(uid, query_id)

			try: #tries the query
				execute_query(query)
				message = "Success! User {0} was added!".format(query_email)
			except Exception as e:
				logging.debug(e)
				if ("1062" in str(e)):
					message = "You're already friends with {0}!".format(query_email)
				else:
					return render_template("friend.html", query=query, error=e)
			

		return render_template("friend.html", name=email, note=message)
		
# @app.route('/album/<uid>/<aid>', methods=['GET', 'POST'])
# @flask_login.login_required
# def album(uid, aid):
# 	email = flask_login.current_user.id
# 	my_uid = getUserIdFromEmail(flask_login.current_user.id)
    
# 	else: #if request is post (user posted some information)
# 		return render_template('friend.html', name=email, friends=friends,data=data)

#default page  
@app.route("/", methods=['GET'])
def home():
	
	if (flask_login.current_user.is_authenticated):
		logged_in_user = flask_login.current_user.id
		user_id = getUserIdFromEmail(logged_in_user)
		logging.debug(logged_in_user)
		return render_template('hello.html', uid=user_id, user=logged_in_user)
	else:
		return render_template('hello.html', user=None)
if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''