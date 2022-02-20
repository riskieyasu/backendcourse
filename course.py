from asyncio import DatagramProtocol
from unicodedata import category
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask import request, jsonify
import base64
from itsdangerous import json
from sqlalchemy import null
from sqlalchemy.sql import func
import datetime
app = Flask(__name__)


app.config['SECRET_KEY']='secret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Raikonen04@localhost:5432/course?sslmode=disable' #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://DB_USER:PASSWORD@HOST/DATABASE'
db = SQLAlchemy(app)
tag = db.Table('tag',
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('status',db.String(20), nullable=False)
) 

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name =db.Column(db.String(20), nullable=False)
	role =db.Column(db.String(20), nullable=False)
	passkey =db.Column(db.String(20), nullable=False)
	courses = db.relationship('Course',secondary = tag, backref = 'user', lazy='joined')
	# courses_completed = db.relationship('Course',secondary = tag_completed, backref = 'user_completed')
class Topic(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name =db.Column(db.String(50), nullable=False)
	course = db.relationship('Course', backref='ownera', lazy='dynamic')
	members  =db.relationship('Course', backref = 'topic')
class Course(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	title =db.Column(db.String(50), nullable=False)
	prerequisite = db.Column(db.Integer, db.ForeignKey('prerequisite.id'), nullable=True)
	topic_id=db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
class Prerequisite(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	prerequisite_1=db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
	prerequisite_2=db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
	prerequisite_3=db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
db.create_all()
db.session.commit()


def auth(a):
    
	e = request.headers['Authorization']
	ee = str(e)
	base64_input = ee[6:].encode("ascii") 

	ag = base64.b64decode(base64_input)
	out = ag.decode("ascii")
	c = out.split(':')
	if a == 'name':
		return c[0]
	elif a == 'passkey':
		return c[1]


@app.route('/index')
def index():
    
	idd = auth('name')
	us = User.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	
	return 'WELCOME', 201

# @app.route('/count')
# def count():
    
# 	namea = User.query.filter_by(name = 'Riski').count()	
	
# 	return str(namea), 201
@app.route('/course', methods=['POST'])
def create_course():
	
	data = request.get_json()
    
	if not 'title' in data or not 'topic_id' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	idd = auth('name')
	us = User.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	u = Course(
			title=data['title'], 
            topic_id=data['topic_id']
		)
	db.session.add(u)
	db.session.commit()
	return {
		'title': u.title, 
        'topic_id': u.topic_id
	}, 201

@app.route('/prerequisite', methods=['POST'])
def create_prerequisite():
	
	data = request.get_json()
    
	if not 'prerequisite_1' in data or not 'prerequisite_2' in data or not 'prerequisite_3 in data':
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	idd = auth('name')
	us = User.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	u = Prerequisite(
			prerequisite_1=data['prerequisite_1'], 
            prerequisite_2=data['prerequisite_2'],
			prerequisite_3=data['prerequisite_3']
		)
	db.session.add(u)
	db.session.commit()
	return {
		'mesage' : 'success'
	}, 201


@app.route('/course/<id>', methods=['PUT'])
def update_course(id):
	data = request.get_json()
	
	if not 'prerequisite' in data :
		return {
			'error': 'Bad Request',
			'message': 'All parameters need to be present'
		}, 400

	idd = auth('name')
	us = User.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'teacher':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	preq = Course.query.filter_by(id=id).first_or_404()
	preq.prerequisite=data.get('prerequisite', Course.prerequisite)
	db.session.commit()
	return {
		'message': 'success'
		}, 201

@app.route('/enroll', methods=['POST'])
def enroll_course():
	
	data = request.get_json()
    
	if not 'id' in data or not 'title' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	cid = Course.query.filter_by(id= data['id']) .first()
	title = Course.query.filter_by(title = data['title']) .first()
		
	if not cid or not title or cid.id != title.id:
		return jsonify({
			'error': 'Bad Request',
			'message': 'no course found'
		}), 400		
	idd = auth('name')
	us = User.query.filter_by(name = idd).first()
	if not us or auth('passkey') != us.passkey or us.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	course = Course.query.filter_by(id = data['id']).first()
	pre = Prerequisite.query.filter_by(id = course.prerequisite).first()
	us_cou_1 = User.query.join(tag).join(Course).filter((tag.c.user_id == us.id) & (tag.c.course_id == pre.prerequisite_1) & (tag.c.status == 'Completed')).first()
	# us_cou_2 = User.query.join(tag).join(Course).filter((tag.c.user_id == us.id) & (tag.c.course_id == pre.prerequisite_2) & (tag.c.status == 'Completed')).first()
	# us_cou_3 = User.query.join(tag).join(Course).filter((tag.c.user_id == us.id) & (tag.c.course_id == pre.prerequisite_3) & (tag.c.status == 'Completed')).first()
	

	if not us_cou_1 and pre.prerequisite_1 != None:
			return jsonify({ 
			'error': 'Bad Request',
			'message': 'not meet minimum requirements'
		}), 400 

	credentials = tag.insert().values(course_id=data['id'], user_id=us.id, status = 'Enrolled')
	db.session.execute(credentials)
	db.session.commit()
	return 'Enrolled', 201




