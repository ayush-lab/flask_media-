from flask import render_template, flash, redirect, url_for,request
from flask import Flask
from Loginform import loginForm, registerForm, EditProfile , PostForm 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,UserMixin, login_user, login_required,logout_user, current_user
from werkzeug.urls import url_parse
from hashlib import md5
from datetime import datetime
from flask_migrate import Migrate
import logging 
import os
from flask_bootstrap import Bootstrap
#from logging.handlers import SMTPHandler


################ CONFIGURATION VARIABLES###################


app=Flask(__name__)
bootstrap=Bootstrap(app) 
app.config['SECRET_KEY']="YES_OK"
app.config[' SQLAlCHEMY_TRACK_MODIFICATIONS ']=True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["POSTS_PER_PAGE"]=3


'''app.config(MAIL_SERVER)=os.environ.get('MAIL_SERVER')
MAIL_PORT=int(os.environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS=os.environ.get("MAIL_USE_TLS") is not None 
MAIL_USERNAME =os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD")
ADMINS =["ayush.verma8750@gmail.com"]
'''
db=SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'          # LOGINMANAGER
login_manager.login_message = " Please, login first to access "

#----------------------------------------------    TABLES	   ----------------------------------------------------------------------------- 

#Creating a follower table 


followers = db.Table('followers', db.Column('follower_id', db.Integer,db.ForeignKey('user.id')), 
								  db.Column('followed_id', db.Integer,db.ForeignKey('user.id')) )

class User(UserMixin, db.Model):

	id =db.Column(db.Integer, primary_key=True)
	username=db.Column(db.String(15),unique=True)
	password=db.Column(db.String(80),unique=True)
	email=db.Column(db.String(80),unique=False) # only until we are on development server
	about_me =db.Column(db.String(140))
	last_seen =db.Column(db.DateTime, default=datetime.utcnow)

	posts=db.relationship('Post',backref='author',lazy='dynamic')  #relationship 1 btw post and user
  
	followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id),secondaryjoin=(followers.c.followed_id==id),
		backref=db.backref('followers',lazy='dynamic'), lazy='dynamic')  #relationship 2 btw user and followers

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest, size)

	def follow(self, user):
		if not self.is_following(user): 
			self.followed.append(user)

	def unfollow(self,user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id==user.id).count()>0

	def followed_posts(self):   #not clear
		followed = Post.query.join(
			followers, (followers.c.followed_id == Post.user_id)).filter(
			followers.c.follower_id == self.id)

		own=Post.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Post.timestamp.desc())
			

class Post(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	body= db.Column(db.String(140))
	timestamp=db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id= db.Column(db.Integer, db.ForeignKey('user.id'))


migrate = Migrate(app,db)
@login_manager.user_loader                #important
def load_user(id):
	return User.query.get(int(id)) 

@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen=datetime.utcnow()
		db.session.commit()


@app.route('/login', methods=["POST","GET"])
def login():
	
	form = loginForm()
	if form.validate_on_submit():
		
		user=User.query.filter_by(username=form.username.data).first()
		if user:
			if check_password_hash(user.password,form.password.data):
				login_user(user)
				return redirect(url_for("index"))

				next_page= request.args.get('next')

				if not next_page or url_parse(next_page).netloc!='':
					next_page=url_for('index')
				
				return redirect(next_page)

		flash("invalid password or username")
		return redirect(url_for('login'))
	#return 'no'

		#flash('Login requested for user {}, remember_me={}'.format(form.username.data, form.remember_me.data))
		#return redirect(url_for('index'))
	return render_template('impulse.html', title='Login-In', header="LOG IN HERE!" ,form=form)




@app.route("/signup", methods=["POST","GET"])
def signup():

	form=registerForm()
	if form.validate_on_submit():
		hashed_password=generate_password_hash(form.password.data , method="sha256")
		new_user= User(username=form.username.data, email=form.email.data,password=hashed_password)
		db.session.add(new_user)
		db.session.commit()
		return redirect(url_for("login"))

		#return '<h1>' + form.username.data + " " + form.password.data + '</h1>'
	return render_template('signupp.html', title='sign-up', header="Sign up here to make account now!" ,form=form)

@app.route('/', methods =["GET","POST"])
@app.route('/index',methods =["GET","POST"])
@login_required
def index():
	form=PostForm()
	if form.validate_on_submit():
		post=Post(body=form.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash("Your post is now live!")
		return redirect(url_for("index"))
	page=request.args.get('page',1,type=int)
	posts = current_user.followed_posts().paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	if posts.has_next:
		next_url=url_for('index',page=posts.next_num) 
	else:
		next_url=None
	if posts.has_prev:
		prev_url=url_for('index', page=posts.prev_num) 
	else:
		prev_url=None


	return render_template('index.html', title = 'homepage', form=form, posts=posts.items, next_url=next_url,prev_url=prev_url)

@app.route("/explore")
@login_required
def explore():
	page=request.args.get('page',1,type=int)
	posts=Post.query.order_by(Post.timestamp.desc()).paginate(
		page, app.config['POSTS_PER_PAGE'], False)

	if posts.has_next:
		next_url=url_for('explore',page=posts.next_num) 
	else:
		next_url =None
	if posts.has_prev:

		prev_url=url_for('explore', page=posts.prev_num) 
	else: 
		prev_url=None 
    				
	return render_template('index.html', title = 'Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)					    																																		

@app.route('/dashboard')
@login_required
def dashboard():
	return "<h1> {current_user.username} created successfully </h1>"

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

####################################################### avatars ##############################################################

@app.route("/dashboard/<username>")
@login_required
def avatar(username):
	user=User.query.filter_by(username=username).first_or_404()

	page=request.args.get('page', 1 , type=int)
	posts=user.posts.order_by(Post.timestamp.desc()).paginate(page,app.config['POSTS_PER_PAGE'], False)
	if posts.has_next:
		next_url=url_for('.avatar', username=user.username,page=posts.next_num)
	else:
		next_url=None
	if posts.has_prev:
		prev_url=url_for('.avatar',username=user.username,page=posts.next_num)
	else:
		prev_url=None

	return render_template('profile.html', user=user, posts=posts.items,next_url=next_url, prev_url=prev_url)


@app.route("/edit_profile", methods = ["GET","POST"])
@login_required
def edit_profile():
	form=EditProfile()
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me=form.about_me.data
		db.session.commit()
		flash('Your changes have been saved')
		return redirect(url_for('edit_profile'))
	elif request.method=="GET":
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me

	return render_template("edit_profile.html", title="edit profile", form=form)

# ---------------------------------------------------ERROR HANDLING --------------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def not_found_error(error):
	return render_template('500.html'),500

'''
if not app.debug:
	if app.config['MAIL_SERVER']==True:
		auth = None
		if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
			auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
		secure = None
		if app.config['MAIL_USE_TLS']:
			secure = ()
		mail_handler = SMTPHandler(
			mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
			fromaddr='no-reply@' + app.config['MAIL_SERVER'],
			toaddrs=app.config['ADMINS'], subject='Microblog Failure',
			credentials=auth, secure=secure)
		mail_handler.setLevel(logging.ERROR)
		app.logger.addHandler(mail_handler)
'''

@app.route('/follow/<username>')
@login_required
def follow(username):
	user=User.query.filter_by(username=username).first()
	if user is None:
		flash('User {} not found.'.format(username))
		return redirect(url_for("dashboard"))
	if user == current_user:
		flash('you cant follow yourself.')
		return redirect(url_for('.avatar', username=username))
	current_user.follow(user)
	db.session.commit()
	flash('you have followed {}!'.format(username))
	return redirect(url_for('.avatar', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('User {} not found.'.format(username))
		return redirect(url_for('dashboard'))
	if user == current_user:
		flash('You cannot unfollow yourself!')
		return redirect(url_for('.avatar', username=username))
	current_user.unfollow(user)
	db.session.commit()
	flash('You have unfollowed {}.'.format(username))
	return redirect(url_for('.avatar', username=username))

#----------------------------------------------------------------------------------------------------------------------------------
