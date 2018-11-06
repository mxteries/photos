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
from werkzeug.utils import secure_filename
import os, base64
import logging

logging.basicConfig(level=logging.DEBUG)
#logging.disable(logging.INFO)

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'potatoes'  # Change this!

# directory that will store all user uploaded photos
UPLOAD_FOLDER = '/home/david/uni/cs460/photoshare/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'david' # david for me, but usually change this to "root"
app.config['MYSQL_DATABASE_PASSWORD'] = '' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

# template docs http://jinja.pocoo.org/docs/2.10/templates/#variables

# the way users are currently defined is very spaghetti. if there is time to refactor:
# https://flask-login.readthedocs.io/en/latest/#configuring-your-application
# https://realpython.com/using-flask-login-for-user-management-with-flask/

# not only that, user.id is the email, rather than the user_id

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
	else:
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
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	test = isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO User (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		usr_path = os.path.join(app.config['UPLOAD_FOLDER'], email)
		os.mkdir(usr_path)
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
	logging.debug("Executing: {0}".format(query))
	cursor.execute(query)
	conn.commit()

#defines a function for extracting the data from a query
def extractData(query):
	logging.debug("Executing: {0}".format(query))
	cursor.execute(query)
	data = cursor.fetchall() # fetches all rows of the query
	return data

def getUserIdFromEmail(email):
	return_id = -1
	try: #tries the query
		cursor.execute("SELECT user_id FROM User WHERE email = '{0}'".format(email))
		return_id = cursor.fetchone()[0]
	except Exception as e:
		logging.warning("Get user id exception {0} for email {1}!".format(e, email))
		return -1
	return return_id

def getEmailFromUserID(uid):
	return_email = -1
	try: #tries the query
		query = "SELECT email FROM User WHERE user_id = '{0}'".format(uid)
		ret_data = extractData(query)
		return_email = ret_data[0][0]
	except Exception as e:
		logging.warning("Get email exception {0} for id {1}!".format(e, uid))
		return -1
	return return_email

def isEmailUnique(email):
	#use this to check if a email has already been registered
	if cursor.execute("SELECT email FROM User WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True


def getAlbumsFromUid(uid):
	query = "SELECT album_id, name FROM User_Album WHERE user_id = {0};".format(uid)
	albums = extractData(query)
	return albums # tuple of tuple ((aid1, name), (aid2, name)) belonging to uid

# get all photos from an album
# serve up images from *the* static directory
def getAlbumPhotos(aid):
	photos = extractData("SELECT photo_path, caption, photo_id FROM Photo WHERE album_id = '{0}'".format(aid))
	return photos # note: list of tuples, [(fullpath, caption, pid), ...]

# return a photo and its caption
def get_a_photo(pid):
	photo = extractData("SELECT photo_path, caption FROM Photo WHERE photo_id = {0}".format(pid))
	return photo[0]

def get_photo_tags(pid):
	tupled_tags = extractData("SELECT word FROM Photo_Tag WHERE photo_id = {0};".format(pid))
	tags = [tag for (tag,) in tupled_tags]
	return tags

def get_pid_from_path(path):
	tupled_pid = extractData("SELECT photo_id FROM Photo WHERE photo_path= {0};".format(path))
	pid = tupled_pid[0][0]
	return pid

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/<uid>')
def profile(uid):
	email = getEmailFromUserID(uid)
	if (email == -1):
		return render_template('message.html', message="The user you searched for was not found")
	myself = False

	if (flask_login.current_user.is_authenticated):
		# check if this is the logged in user's profile
		logged_in_user = flask_login.current_user.id
		if (logged_in_user == email):
			myself = True

	return render_template('profile.html', name=email, myself=myself, uid=uid)

@app.route('/friend', methods=['GET', 'POST'])
@flask_login.login_required
def find_users():
	email = flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET': # if request is get (user navigated to the URL)
		# optional: change fname lname to be not null and display those
		data = extractData("SELECT user_id, email FROM User WHERE user_id <> {0};".format(uid))
		# friends is all the ppl current_user is following
		friends = extractData("SELECT user_id, email FROM (SELECT * FROM Friendship WHERE follower_user_id={0}) temp JOIN User ON temp.followed_user_id = User.user_id;".format(uid)) 
	
		return render_template('friend.html', name=email, friends=friends, data=data)
    
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
				logging.warning(e)
				if ("1062" in str(e)):
					message = "You're already friends with {0}!".format(query_email)
				else:
					return render_template("friend.html", query=query, error=e)
			

		return render_template("friend.html", name=email, note=message)

# this route should display links to all albums by a user
# user should not be able to post if theyre not logged in (can't see the form)
@app.route('/<uid>/album', methods=['GET', 'POST'])
def album(uid):
	# verify if uid is valid
	email = getEmailFromUserID(uid)
	if (email == -1):
		return render_template('message.html', message="The user you searched for was not found")

	if request.method == 'GET':
		myself = False
		if (flask_login.current_user.is_authenticated):
		# check if this is the logged in user's profile albums
			logged_in_user = flask_login.current_user.id
			if (logged_in_user == email):
				myself = True
		
		user_albums = getAlbumsFromUid(uid)
		logging.debug("All albums of user {0}: {1}".format(uid, user_albums))
		return render_template('album.html', albums=user_albums, uid=uid, myself=myself, user=email)

	else: #if request is post (user posted some information)
		message = "Nothing happened! Try again"

		#get the user searched from the 'USER_EMAIL' row of the form
		album_name = request.form['USER_ALBUM']
		if (len(album_name) > 100):
			message = "Name is too long, limit to 100 characters"
		else:
			query = "INSERT INTO User_Album(user_id, name) VALUES({0}, \"{1}\");".format(uid, album_name)
			try: #tries the query
				execute_query(query)
				message = "Success! Album {0} was created!".format(album_name)
			except Exception as e:
				logging.warning(e)
				if ("1062" in str(e)):
					message = "You already have album called {0}!".format(album_name)
				else:
					return render_template("album.html", query=query, error=e)
		user_albums = getAlbumsFromUid(uid)
		return render_template("album.html", uid=uid, user=getEmailFromUserID(uid), albums=user_albums, message=message, myself=True)

# How this works:
# every photo is stored in mysql as <email>/<photoname>
# this route will locate that photo from the static folder, and serve it up in html
@app.route('/<uid>/album/<aid>',  methods=['GET', 'POST'])
def list_photos(uid, aid):
	email = getEmailFromUserID(uid)
	if (email == -1):
		return render_template('message.html', message="The user you searched for was not found")

	if request.method == 'GET':
		myself = False
		if (flask_login.current_user.is_authenticated):
		# check if this is the logged in user's profile albums
			logged_in_user = flask_login.current_user.id
			if (logged_in_user == email):
				myself = True

		album_photos = getAlbumPhotos(aid) # ((path1, caption, pid1), (path2, caption, pid2))
		logging.debug("All photos of user {0}: {1}".format(uid, album_photos))
		
		return render_template('photo.html', photos=album_photos, aid=aid, uid=uid, myself=myself, user=email)

# upload a photo to an album
# how it works:
# every photo gets stored in photoshare/static/<email>/<photoname>
# we save <email>/<photoname> in mysql's Photo table (photo_path column)
# todo: add tags to the upload interface
@app.route('/<uid>/album/<aid>/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(uid, aid):
	if request.method == 'POST':
		photofile = request.files['photo']
		caption = request.form.get('caption')
		tags = request.form.get('tag')
		message = "Nothing happened, try again"
		if photofile and allowed_file(photofile.filename):
			filename = secure_filename(photofile.filename)
			photo_filepath = os.path.join(getEmailFromUserID(uid), filename)
			fullpath = os.path.join(app.config['UPLOAD_FOLDER'], photo_filepath)
			photofile.save(fullpath)
			logging.debug("Uploaded {0} to {1}".format(filename, fullpath))

			mysql_photo_path = os.path.join('/static', photo_filepath) # what gets stored in mysql
			try:
				query = "INSERT INTO Photo (photo_path, album_id, caption) VALUES ('{0}', ' {1}', '{2}');".format(mysql_photo_path, aid, caption)
				execute_query(query)
				insert_tags(tags, get_pid_from_path(mysql_photo_path))
				message = "Success!! Photo Uploaded!"
			except Exception as e:
				logging.warning(e)
				if ("1062" in str(e)):
					message = "You've already uploaded a file with that filename!"
				else:
					return render_template("message.html", query=query, error=e)

		else:
			message = "Upload failed, did you submit anything?"
		return render_template('photo.html', user=getEmailFromUserID(uid), uid=uid, aid=aid, message=message, photos=getAlbumPhotos(aid), myself=True)
	#The method is GET so we return a HTML form to choose an album to upload the photo.
	else:
		return render_template('upload.html', aid=aid, uid=uid)


# View a photo to leave a like or comment
@app.route('/<uid>/album/<aid>/<pid>')
def view_photo(uid, aid, pid):
	email = getEmailFromUserID(uid)
	if (email == -1):
		return render_template('message.html', message="The user you searched for was not found")
	
	user = "Anonymous"
	myself = False
	if (flask_login.current_user.is_authenticated):
	# check if this is the logged in user's profile albums
		logged_in_user = flask_login.current_user.id
		if (logged_in_user == email):
			myself = True
			user = email

	photo, caption = get_a_photo(pid)
	tags = get_photo_tags(pid)
	logging.debug("Viewing user {0}'s photo: {1} with tags {2}".format(user, photo, tags))
	
	return render_template('a_photo.html', myself=myself, user=user, photo=photo, uid=uid, aid=aid, pid=pid, caption=caption, tags=tags)


def insert_tags(tag_str, pid):
	tags = tag_str.split()
	if tags: # if tag_str isnt "" or " "
		for tag in tags:
			logging.debug("Associating tag {0} with photo pid {1}".format(tag, pid))
			query = "INSERT INTO Photo_Tag VALUES('{0}', {1});".format(tag, pid)
			execute_query(query)

@app.route('/<uid>/album/<aid>/<pid>/tag', methods=['POST'])
def handle_insert_tags(uid, aid, pid):
	if request.method == 'POST':
		tags = request.form['USER_TAGS']
		insert_tags(tags, pid)
		return redirect(url_for('view_photo', uid=uid, aid=aid, pid=pid))

# view a "virtual album" of all photos tagged with <tag>
@app.route("/tag/view/<tag>")
def tagged_photos(tag):
	query = "SELECT photo_path FROM Photo_Tag NATURAL JOIN Photo WHERE word = \"{0}\";".format(tag)
	photos = extractData(query)
	logging.debug("photos looks like: {0}".format(photos))
	return render_template("tag.html", tag=tag, photos=photos)

@app.route("/tag", methods=['POST'])
def display_searched_tags():
	# user searched for photos that have all of (x) tags
	# oh my goodness this query is so godlike, 
	# source: https://stackoverflow.com/questions/13821345/mysql-select-ids-that-match-all-tags

	tags = request.form['SEARCH_TAG'].split()
	num_tags = len(tags)
	
	tag_group = "("
	for index, tag in enumerate(tags):
		if (index < (num_tags - 1)):
			tag = '"' + tag + '"' + ","
		else:
			tag = '"' + tag + '"'
		tag_group += tag
	tag_group += ")"
	logging.debug(tag_group)
	query = "SELECT photo_path FROM (SELECT photo_id FROM Photo_Tag WHERE word IN {0} GROUP BY photo_id HAVING COUNT(*) = {1}) tagged natural join Photo;".format(tag_group, num_tags)
	photos = extractData(query)

	logging.debug(photos)
	return render_template("tag.html", tag=request.form['SEARCH_TAG'], photos=photos)


#default page  
@app.route("/", methods=['GET'])
def home():
	if (flask_login.current_user.is_authenticated):
		logged_in_user = flask_login.current_user.id
		user_id = getUserIdFromEmail(logged_in_user)
		logging.debug("{0} is logged in".format(logged_in_user))
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