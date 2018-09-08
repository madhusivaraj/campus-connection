from flask import Flask, render_template, url_for
from passlib.hash import sha256_crypt
import pymysql
import yaml

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
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

@app.route('/register')
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
		flash('Congrats! You are now a registered hacker.')
		return redirect(url_for('login'))
	return render_template('register.html')
    
if __name__ == '__main__':
	app.run(debug=True)
