######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
# Perfected by: David Shen <dshen1@bu.edu>
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
from datetime import date
logging.basicConfig(level=logging.DEBUG)
#logging.disable(logging.INFO)

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'potatoes'  # Change this!

# directory that will store all user uploaded photos
UPLOAD_FOLDER = '/home/david/uni/cs460/photoshare/static'
pro_pic_folder_name = "profile_picture"
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
		logging.warning("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))
	test = isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO User (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		usr_path = os.path.join(app.config['UPLOAD_FOLDER'], email)
		pro_pic_dir = os.path.join(usr_path, pro_pic_folder_name)
		os.mkdir(usr_path)
		os.mkdir(pro_pic_dir)
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

# 2018-11-06
def get_date():
	return str(date.today())

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
	tupled_pid = extractData("SELECT photo_id FROM Photo WHERE photo_path = '{0}';".format(path))
	pid = tupled_pid[0][0]
	return pid

def get_uid_from_pid(pid):
	tupled_uid = extractData("SELECT user_id FROM Photo NATURAL JOIN User_Album WHERE photo_id = {0};".format(pid))
	uid = tupled_uid[0][0]
	return uid

def get_uid_from_aid(aid):
	tupled_uid = extractData("SELECT user_id FROM User_Album NATURAL JOIN User WHERE album_id = {0};".format(aid))
	uid = tupled_uid[0][0]
	return uid

def get_photo_comments(pid):
	tupled_comments = extractData("SELECT email, text, date FROM Photo_Comment where photo_id = {0}".format(pid))
	# replace mysqls NULL with anonymous
	tupled_comments = [("Anonymous" if email is None else email, text, date) for (email, text, date) in tupled_comments]
	return tupled_comments # ((bob, hi, 2018-01-12), (ted, bye, 2018-5-4), ...)

def get_number_of_likes(pid):
	query = "SELECT count(user_id) FROM Photo_Like WHERE photo_id = {0};".format(pid)
	tupled_num = extractData(query)
	return tupled_num[0][0]

def get_users_who_liked(pid):
	query = "SELECT user_id, email FROM Photo_Like NATURAL JOIN User WHERE photo_id = {0};".format(pid)
	tuple_of_users = extractData(query) # ((1, ash@bu.edu), (2, test@bu.edu), ...)
	return tuple_of_users

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

# todo, if aid doesn't exist, handle that exception
@app.route('/album/<aid>/delete', methods=['POST'])
@flask_login.login_required
def delete_album(aid):
	album_owner = get_uid_from_aid(aid)
	message = "You are not authorized to do that"
	if (flask_login.current_user.is_authenticated):
		logged_in_user_id = getUserIdFromEmail(flask_login.current_user.id)
		logging.debug("User {0} is trying to delete album {1}".format(logged_in_user_id, aid))
		if logged_in_user_id == album_owner:
			query = "DELETE FROM User_Album where album_id = {0};".format(aid)
			execute_query(query)
			message = "Album deleted."
	return render_template('message.html', message=message)

# How this works:
# every photo is stored in mysql as <email>/<photoname>
# this route will locate that photo from the static folder, and serve it up in html
@app.route('/<uid>/album/<aid>',  methods=['GET'])
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
@app.route('/photo/<pid>')
def view_photo(pid):

	photo_owner = getEmailFromUserID(get_uid_from_pid(pid))
	user = "Anonymous"
	myself = False

	# check if this is the logged in user's photo
	if (flask_login.current_user.is_authenticated):
		logged_in_user = flask_login.current_user.id
		user = logged_in_user # if this is my photo, grant access controls. else, just tell them who they are
		if (logged_in_user == photo_owner):
			myself = True

	photo, caption = get_a_photo(pid)
	tags = get_photo_tags(pid)
	comments = get_photo_comments(pid)
	num_likes = get_number_of_likes(pid)
	logging.debug("Viewing {0}'s photo: {1} as user {2} with tags {3} and comments {4}".format(photo_owner, user, photo, tags, comments))
	
	return render_template('a_photo.html', myself=myself, user=user, owner=photo_owner, photo=photo, pid=pid, caption=caption, likes=num_likes, comments=comments, tags=tags)

# todo, if pid doesn't exist, handle that exception
@app.route('/photo/<pid>/delete', methods=['POST'])
@flask_login.login_required
def delete_photo(pid):
	photo_owner = get_uid_from_pid(pid)
	message = "You are not authorized to do that"
	if (flask_login.current_user.is_authenticated):
		logged_in_user_id = getUserIdFromEmail(flask_login.current_user.id)
		logging.debug("User {0} is trying to delete photo {1}".format(logged_in_user_id, pid))
		if logged_in_user_id == photo_owner:
			query = "DELETE FROM Photo where photo_id = {0};".format(pid)
			execute_query(query)
			message = "Photo deleted."
	return render_template('message.html', message=message) 

# user can like his own photo
# any user may only like a photo once! 
@app.route("/photo/<pid>/likes", methods=['GET','POST'])
@flask_login.login_required
def like_photo(pid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		action = request.form.get('ACTION')
		if action == "LIKE":
			try:
				query = "INSERT INTO Photo_Like VALUES ({0}, {1});".format(uid, pid)
				execute_query(query)
				logging.debug("Added a like for photo {0}".format(pid))
			except Exception as e:
				logging.warning(e)
				return render_template("message.html", query=query, error=e)
		elif action == "UNLIKE":
			try:
				query = "DELETE FROM Photo_Like WHERE user_id = {0} AND photo_id = {1};".format(uid, pid)
				execute_query(query)
				logging.debug("Removed a like for photo {0}".format(pid))
			except Exception as e:
				logging.warning(e)
				return render_template("message.html", query=query, error=e)
		else:
			return render_template('message.html', message="UNDEFINED ACTION {0}".format(action)) 
		return redirect(url_for('view_photo', pid=pid))
	else:
		user_likes = get_users_who_liked(pid)
		logging.debug("Here are the users who liked {0}: {1}".format(pid, user_likes))
		return render_template('like.html', likes=user_likes, pid=pid) 

#myself cant comment on his photo
@app.route("/photo/<pid>/comment", methods=['POST'])
def comment(pid):
	photo_owner = getEmailFromUserID(get_uid_from_pid(pid))
	commenter = "NULL"
	myself = False

	# check if this is my photo, and set who's commenting
	if (flask_login.current_user.is_authenticated):
		logged_in_user = flask_login.current_user.id
		commenter = '"' + logged_in_user + '"'
		if (logged_in_user == photo_owner):
			myself = True

	if request.method == 'POST':
		some_comment = request.form['USER_COMMENT']
		# if this is my comment
		logging.debug("User {0} tries to post on photo belonging to {1}".format(commenter, photo_owner))
		if myself:
			return render_template('message.html', message="You can't comment on your own photo. Blame the requirements")
		else:
			try:
				query = 'INSERT INTO Photo_Comment(photo_id, text, date, email) values ({0}, "{1}", "{2}", {3});'
				query = query.format(pid, some_comment, get_date(), commenter)
				execute_query(query)
			except Exception as e:
				logging.warning(str(e))
				return render_template("message.html", query=query, error=e)

		return redirect(url_for('view_photo', pid=pid))


def insert_tags(tag_str, pid):
	tags = tag_str.split()
	if tags: # if tag_str isnt "" or " "
		for tag in tags:
			logging.debug("Associating tag {0} with photo pid {1}".format(tag, pid))
			query = "INSERT INTO Photo_Tag VALUES('{0}', {1});".format(tag, pid)
			execute_query(query)

@app.route('/photo/<pid>/tag', methods=['POST'])
def handle_insert_tags(pid):
	if request.method == 'POST':
		tags = request.form['USER_TAGS']
		insert_tags(tags, pid)
		return redirect(url_for('view_photo', pid=pid))

# view a "virtual album" of all photos tagged with <tag>
@app.route("/tag/view/<tag>")
def tagged_photos(tag):
	query = "SELECT photo_path, photo_id FROM Photo_Tag NATURAL JOIN Photo WHERE word = \"{0}\";".format(tag)
	photos = extractData(query)
	logging.debug("photos looks like: {0}".format(photos))
	return render_template("tag.html", tag=tag, photos=photos)

# view a "virtual album" of all photos that contain a number of tags 
# specified in the url query ie request.args
# if request.args has a toggle to show only "my" photos
# we display only the photos belonging to the logged in user
@app.route("/tag", methods=['GET'])
def display_searched_tags():
	# user searched for photos that have all of (x) tags
	# oh my goodness this query is so godlike, 
	# source: https://stackoverflow.com/questions/13821345/mysql-select-ids-that-match-all-tags
	logging.debug(request.args)
	tags = request.args['SEARCH_TAG'].split()

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
	query = ("SELECT photo_path, photo_id FROM " + 
		"(SELECT photo_id FROM Photo_Tag WHERE word IN {0} GROUP BY photo_id HAVING COUNT(*) = {1}) tagged " + 
		"natural join Photo;")
	query = query.format(tag_group, num_tags)
	
	my_photo_toggle = False
	# now if we want to only see OUR photos, have to modify query a bit
	if 'TOGGLE' in request.args:
		if request.args['TOGGLE'] == "MY PHOTOS":
			if (flask_login.current_user.is_authenticated):
				my_photo_toggle = True
				logged_in_user = getUserIdFromEmail(flask_login.current_user.id)
				query = ("SELECT photo_path, photo_id FROM " +
				"(SELECT photo_id FROM Photo_Tag WHERE word IN {0} GROUP BY photo_id HAVING COUNT(*) = {1}) tagged " +
				"natural join Photo natural join User_Album " +
				"where user_id = {2};")
				query = query.format(tag_group, num_tags, logged_in_user)
			else: 
				return render_template('unauth.html') 

	photos = extractData(query)
	return render_template("tag.html", tag=request.args['SEARCH_TAG'], photos=photos, show_my_photos=my_photo_toggle)

# given a photo, deleles a tag from the photo
@app.route('/photo/<pid>/tag/delete/<word>', methods=['POST'])
@flask_login.login_required
def delete_tag(pid, word):
	photo_owner = get_uid_from_pid(pid)
	if (flask_login.current_user.is_authenticated):
		logged_in_user_id = getUserIdFromEmail(flask_login.current_user.id)
		logging.debug("User {0} is trying to delete photo {1}'s tag {2}".format(logged_in_user_id, pid, word))
		if logged_in_user_id == photo_owner:
			query = "DELETE FROM Photo_Tag where word = '{0}' and photo_id = {1};".format(word, pid)
			execute_query(query)
	return redirect(url_for('view_photo', pid=pid))


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