from __future__ import print_function
from flask import Flask, render_template, url_for, session, request, flash, redirect
from passlib.hash import sha256_crypt
import pymysql
import yaml
import collections
#import datetime
#from googleapiclient.discovery import build
#from httplib2 import Http
#from oauth2client import file, client, tools

app = Flask(__name__)

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
"""
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
"""

@app.route('/matches', methods=['GET', 'POST'])
def matches():
	username=session['username']
	  
	  #get list of curr user's time slots from usertots
	userTimes = []
	matchingTimes = []
	timesArr = ["12:00 AM", "12:30 AM", "1:00 AM", "1:30 AM", "2:00 AM", "2:30 AM", "3:00 AM", "3:30 AM",
	   			"4:00 AM", "4:30 AM", "5:00 AM", "5:30 AM", "6:00 AM", "6:30 AM", "7:00 AM", "7:30 AM",
	   			"8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
	   			"12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM",
	   			"4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM",
	   			"8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM"]
	  
	num=0
	  
	cur = myApp.cursor()
	  
	cur.execute("SELECT userID FROM user WHERE username=%s", [username])
	  
	userID = cur.fetchone()['userID']
	  
	cur.execute("SELECT * FROM usertots WHERE userID=%s", [userID])
	rows = cur.fetchall()
	for row in rows:
		userTimes.append(row['tsID'])
	l = []
	myDict = dict()
	cur.execute("SELECT * FROM user WHERE userID != %s", [userID])
	for user in cur.fetchall():
    	# check if user has time slots in common
    	# make dictionary of userIDs and list of matches
		currID = user['userID']
		currUser = user['username']
		cur.execute("SELECT * FROM usertots WHERE userID=%s", [currID])
		allUsers = cur.fetchall()
		for row in allUsers:
			if row['tsID'] in userTimes:
				cur.execute("SELECT ts FROM timeslots WHERE tsID=%s",[row['tsID']])
				l.append(cur.fetchone()['ts'])

		myDict[currUser] = l
		l = []

    # sort dictionary
	results = collections.OrderedDict()
	for k in sorted(myDict, key = lambda k: len(myDict[k]), reverse=True):
		if len(myDict[k]) > 0:
			num = num + 1
			results[k] = myDict[k]

	return render_template('matches.html', num=num, results=results, username=username)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
	username = session['username']
	timeslots = None
	days = collections.OrderedDict()
	week = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']
	for i in range(0, 7):
		days[i] = week[i]

	i = 0
	times = collections.OrderedDict()
	cur = myApp.cursor()
	cur.execute("SELECT * FROM timeslots")
	rows = cur.fetchall()
	for row in rows:
		times[i] = row['ts']
		i = i + 1

	timesArr = ["12:00 AM", "12:30 AM", "1:00 AM", "1:30 AM", "2:00 AM", "2:30 AM", "3:00 AM", "3:30 AM",
			"4:00 AM", "4:30 AM", "5:00 AM", "5:30 AM", "6:00 AM", "6:30 AM", "7:00 AM", "7:30 AM",
			"8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
			"12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM",
			"4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM",
			"8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM"]

	if request.method == 'POST':
		timeslots = request.form.getlist('timeslots[]')
		#print(timeslots)
		cur.execute("SELECT userID FROM user WHERE username=%s", [username])
		userID = cur.fetchone()['userID']
		for i in range(0, len(timeslots)):
			cur.execute("SELECT tsID FROM timeslots WHERE ts=%s",[timeslots[i]])
			tsID = cur.fetchone()['tsID']
			cur.execute("INSERT INTO usertots VALUES(%s, %s)", [userID, tsID])
			myApp.commit()
		cur.close()
		return redirect('matches')

	return render_template('profile.html', username=username, days=days, times=times, timesArr=timesArr)

@app.route('/profile', defaults={'username': None})
@app.route('/profilePage/<username>')
def profilePage(username):
	if username == None:
		username = session['username']
	times = []
	cur = myApp.cursor()
	cur.execute("SELECT userID FROM user WHERE username=%s", [username])
	userID = cur.fetchone()['userID']
	#print(str(username)+' '+str(userID))
	cur.execute("SELECT * FROM usertots WHERE userID=%s", [userID])
	rows = cur.fetchall()
	for row in rows:
		tsID = row['tsID']
		cur.execute("SELECT ts FROM timeslots WHERE tsID=%s", [tsID])
		time = cur.fetchone()['ts']
		times.append(parseTime(time))


	return render_template('profilePage.html', username=username, times=times)

def parseTime(result):
	timeSlot = ''
	if result[0] == 'M':
		timeSlot = timeSlot + "Monday"
		result = result[1:]
	elif result[0:2] == 'TH':
		timeSlot = timeSlot + "Thursday"
		result = result[2:]
	elif result[0] == 'T':
		timeSlot = timeSlot + "Tuesday"
		result = result[1:]
	elif result[0] == 'W':
		timeSlot = timeSlot + "Wednesday"
		result = result[1:]
	elif result[0] == 'F':
		timeSlot = timeSlot + "Friday"
		result = result[1:]
	elif result[0:2] == 'SU':
		timeSlot = timeSlot + "Sunday"
		result = result[2:]
	elif result[0] == 'S':
		timeSlot = timeSlot + "Saturday"
		result = result[1:]

	print(timeSlot, result)
	result = result.replace(":", "")

	timeKey = ['0', '030', '1', '130', '2', '230', '3', '330', '4', '430', '5', '530','6','630','7','730','8','830','9','930','10','1030','11','1130','12','1230','13','1330','14','1430','15','1530', '16', '1630', '17', '1730', '18', '1830', '19', '1930', '20', '2030', '21','2130', '22', '2230', '23', '2330']
	timesArr = ["12:00 AM", "12:30 AM", "1:00 AM", "1:30 AM", "2:00 AM", "2:30 AM", "3:00 AM", "3:30 AM",
			"4:00 AM", "4:30 AM", "5:00 AM", "5:30 AM", "6:00 AM", "6:30 AM", "7:00 AM", "7:30 AM",
			"8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
			"12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM",
			"4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM",
			"8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM", "12:00 AM"]

	timeDict = collections.OrderedDict()
	for i in range(0, len(timeKey)):
		timeDict[timeKey[i]] = timesArr[i]

	return timeSlot +" " +timeDict[result] 


app.secret_key = 'MVB79L'

if __name__ == '__main__':
	app.run(debug=True)
