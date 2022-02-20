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
	courses = db.relationship('Course',secondary = tag, backref = 'user')
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
	namea = User.query.filter_by(name = idd).first()
	if not namea or auth('passkey') != namea.passkey or namea.role != 'user':
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
    
	if not 'title' in data or not 'prerequisite' in data  or not 'topic_id' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	idd = auth('name')
	namea = User.query.filter_by(name = idd).first()
	if not namea or auth('passkey') != namea.passkey or namea.role != 'admin':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
		
	u = Course(
			title=data['title'], 
			prerequisite=data['prerequisite'],
			status= 'Couse_List',
            topic_id=data['topic_id']
		)
	db.session.add(u)
	db.session.commit()
	return {
		'title': u.title, 
        'topic_id': u.topic_id
	}, 201

@app.route('/enroll', methods=['POST'])
def enroll_course():
	
	data = request.get_json()
    
	if not 'id' in data or not 'title' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'all data not given'
		}), 400    
	idd = auth('name')
	namea = User.query.filter_by(name = idd).first()
	if not namea or auth('passkey') != namea.passkey or namea.role != 'user':
		return jsonify({ 
			'error': 'Bad Request',
			'message': 'not authenthicated'
		}), 400 
	nameaa = Course.query.filter_by(title = data['title']).first()	
	u = Course(
			title=data['title'], 
			prerequisite=nameaa.prerequisite,
			status= 'Enrolled',
            topic_id=nameaa.topic_id
		)
	
	db.session.add(u)
	descending = Course.query.order_by(Course.id.desc())
	last_item = descending.first()
	credentials = tag.insert().values(course_id=last_item.id, user_id=namea.id)
	db.session.execute(credentials)
	db.session.commit()
	return 'Enrolled', 201




