from __future__ import print_function
from flask import Flask, render_template, url_for, session, request, flash, redirect
from passlib.hash import sha256_crypt
import pymysql
import yaml
import collections
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

app = Flask(__name__)

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

db = yaml.load(open('db.yaml'))
myApp = pymysql.connect(host=db['mysql_host'], user=db['mysql_user'], password=db['mysql_password'], db=db['mysql_db'], charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


@app.route('/')
def index():
	username=None
	if 'username' in session:
		username = session['username']
		# check if user filled out profile + has matches
		"""
		cur = myApp.cursor()
		cur.execute("SELECT userID FROM user WHERE username=%s", [username])
		userID = cur.fetchone()['userID']
		cur.execute("SELECT hackathonID FROM usertohackathon WHERE userID=%s", [userID])
		if cur.fetchone() is not None:
			return render_template('index.html', username=username, profile=profile)
		return render_template('index.html', username=username)
		"""
	return render_template('index.html', username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
	error = []
	isIssue = False
	if request.method == 'POST':
		# fetch form data
		userDetails = request.form
		username = userDetails['username']
		email = userDetails['email']
		password = userDetails['password']
		confirm_password = userDetails['confirm_password']

		cur = myApp.cursor()
		cur.execute("SELECT * FROM user WHERE username = %s", [username])

		#error handling
		if cur.fetchone() is not None:
			error.append('Please choose a different username.')
			isIssue = True

		cur.execute("SELECT * FROM user WHERE email = %s", [email])

		if cur.fetchone() is not None:
			error.append('Email already registered.')
			isIssue = True

		if password != confirm_password:
			error.append('Passwords do not match.')
			isIssue = True

		if isIssue: # if any errors
			return render_template('register.html', error = error)

		# if no errors, add to database
		cur.execute("INSERT INTO user(email, username, password) VALUES(%s, %s, %s)", [email, username, sha256_crypt.encrypt(password)])
		myApp.commit()
		cur.close()
		flash('Congrats! You are now a registered user.')
		return redirect(url_for('login'))
	return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if 'username' in session:
		return redirect(url_for('index'))
	if request.method == 'POST':
		username_form  = request.form['username']
		password_form  = request.form['password']
		cur = myApp.cursor()
		cur.execute("SELECT COUNT(1) FROM user WHERE username = %s;", [username_form]) # CHECKS IF USERNAME EXISTS
		if cur.fetchone() is not None:
			cur.execute("SELECT password FROM user WHERE username = %s;", [username_form]) # FETCH THE PASSWORD
			for row in cur.fetchall():
				if sha256_crypt.verify(password_form, row['password']):
					session['username'] = request.form['username']
					cur.close()
					return redirect(url_for('index'))
				else:
					error = "Wrong password"
		else:
			error = "Username not found"
		cur.close()
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))




@app.route('/calendar', methods=['GET', 'POST'])
def calendar():

    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                    maxResults=10, singleEvents=True,
                                    orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    username=session['username']
    if request.form == 'POST':
        return render_template('calendar.html', username=username)

    return render_template('calendar.html', username=username)

@app.route('/matches', methods=['GET', 'POST'])
def matches():
    username=session['username']
    if request.form == 'POST':
        return render_template('matches.html', username=username)
    return render_template('matches.html', username=username)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session['username']
    timeslots=None
    cur = myApp.cursor()
    days = collections.OrderedDict()
    week = ['SU', 'M', 'T', 'W', 'TH', 'F', 'S']
    for i in range(0, 6):
    	days[i] = week[i]

    i = 0
    times = collections.OrderedDict()
    cur.execute("SELECT * FROM timeslots")
    rows = cur.fetchall()
    for row in rows:
    	times[i] = row['ts']
    	i = i + 1

    if request.form == 'POST':
        timeslots = request.form.getlist('timeslots[]')
        return render_template('profile.html', timeslots=timeslots, username=username, times=times, days=days)
    return render_template('profile.html', username=username, days=days, timeslots=timeslots, times=times)

app.secret_key = 'MVB79L'

if __name__ == '__main__':
	app.run(debug=True)
