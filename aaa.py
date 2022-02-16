from flask_sqlalchemy import SQLAlchemy
import uuid
from flask import Flask
from flask import request, jsonify
app = Flask(__name__)
import base64

app.config['SECRET_KEY']='secret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Raikonen04@localhost:5432/riski?sslmode=disable' #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://DB_USER:PASSWORD@HOST/DATABASE'
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    name =db.Column(db.String(20), nullable=False)
    email =db.Column(db.String(28), nullable=False, unique=True)
    public_id =db.Column(db.String, nullable=False)
    is_admin =db.Column(db.Boolean, default=False) #untuk otorisasi
    name =db.relationship('Todo', backref='owner', lazy='dynamic') #agar terhubung ke model to-do
    #mengambil 3 nilai, yaitu:
    #jenis bidang
    #backref atau variabel untuk mereferensikan model pengguna dalam model to-do
    #lazy adalah bagaimana data dimuat)

    def _repr_(self):
        return f'User <{self.email}>'

class Todo(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(20), nullable=False)
	is_completed = db.Column(db.Boolean, default=False)
	public_id = db.Column(db.String, nullable=False)
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	
	def _repr_(self):
		return f'Todo: <{self.name}>'

db.create_all()
db.session.commit() 
@app.route('/')
def home():
	return {
		'message': 'Welcome to building RESTful APIs with Flask and SQLAlchemy'
	}


@app.route('/users/')
def get_users():
	a = User.query.all()
	for user in a:
		dictt = {
			"id": user.public_id,  
		    "name": user.name, 
			"email": user.email,
			"is admin": user.is_admin
	    }
	return dictt
	
@app.route('/users/<id>/')
def get_user(id):
	print(id)
	user = User.query.filter_by(public_id=id).first_or_404()
	return {
		'id': user.public_id, 
		'name': user.name, 
		'email': user.email, 'is admin': user.is_admin
		}

@app.route('/users/', methods=['POST'])
def create_user():
	data = request.get_json()
	if not 'name' in data or not 'email' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name or email not given'
		}), 400
	if len(data['name']) < 4 or len(data['email']) < 6:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name and email must be contain minimum of 4 letters'
		}), 400
	u = User(
			name=data['name'], 
			email=data['email'],
			is_admin=data.get('is admin', False),
			public_id=str(uuid.uuid4())
		)
	db.session.add(u)
	db.session.commit()
	return {
		'id': u.public_id, 'name': u.name, 
		'email': u.email, 'is admin': u.is_admin 
	}, 201

@app.route('/users/<id>/', methods=['PUT'])
def update_user(id):
	data = request.get_json()
	if 'name' not in data:
		return {
			'error': 'Bad Request',
			'message': 'Name field needs to be present'
		}, 400
	user = User.query.filter_by(public_id=id).first_or_404()
	user.name=data['name']
	if 'is admin' in data:
		user.is_admin=data['admin']
	db.session.commit()
	return jsonify({
		'id': user.public_id, 
		'name': user.name, 'is admin': user.is_admin,
		'email': user.email
		})

@app.route('/users/<id>/', methods=['DELETE'] )
def delete_user(id):
	user = User.query.filter_by(public_id=id).first_or_404()
	db.session.delete(user)
	db.session.commit()
	return {
		'success': 'Data deleted successfully'
	}

@app.route('/todos/')
def get_todos():
	return jsonify([
		{ 
			'id': todo.public_id, 'name': todo.name,
			'owner': {
				'name': todo.owner.name,
				'email': todo.owner.email,
				'public_id': todo.owner.public_id
			}
		} for todo in Todo.query.all()
	])

@app.route('/todos/<id>')
def get_todo(id):
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	return jsonify({ 
			'id': todo.public_id, 'name': todo.name,
			'owner': {
				'name': todo.owner.name,
				'email': todo.owner.email,
				'public_id': todo.owner.public_id
			}
		})

@app.route('/todos/', methods=['POST'])
def create_todo():
	data = request.get_json()
	if not 'name' in data or not 'email' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name of todo or email of creator not given'
		}), 400
	if len(data['name']) < 4:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name of todo contain minimum of 4 letters'
		}), 400

	user=User.query.filter_by(email=data['email']).first()
	if not user:
		return {
			'error': 'Bad request',
			'message': 'Invalid email, no user with that email'
		}
	is_completed = data.get('is completed', False)
	todo = Todo(
		name=data['name'], user_id=user.id,
		is_completed=is_completed, public_id=str(uuid.uuid4())
	)
	db.session.add(todo)
	db.session.commit()
	return {
		'id': todo.public_id, 'name': todo.name, 
		'completed': todo.is_completed,
		'owner': {
			'name': todo.owner.name,
			'email': todo.owner.email,
			'is admin': todo.owner.is_admin 
		} 
	}, 201

@app.route('/todos/<id>/', methods=['PUT'])
def update_todo(id):
	data = request.get_json()
	print(data)
	print('is completed' in data)
	if not 'name' in data or not 'completed' in data:
		return {
			'error': 'Bad Request',
			'message': 'Name or completed fields need to be present'
		}, 400
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	todo.name=data.get('name', todo.name)
	if 'is completed' in data:
		todo.is_completed=data['is completed']
	db.session.commit()
	return {
		'id': todo.public_id, 'name': todo.name, 
		'is completed': todo.is_completed,
		'owner': {
			'name': todo.owner.name, 'email': todo.owner.email,
			'is admin': todo.owner.is_admin 
		} 
	}, 201

@app.route('/todos/<id>/', methods=['DELETE'] )
def delete_todo(id):
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	db.session.delete(todo)
	db.session.commit()
	return {
		'success': 'Data deleted successfully'
	}

if __name__ == '_main_':
	app.run()




















# from flask import Flask, request_started
# from flask import request
# from flask import abort
# from collections import Counter
# from flask import Response
# from flask import render_template
# from flask import current_app, flash, jsonify, make_response, redirect, request, url_for
# import base64
# app = Flask(__name__)
# @app.route("/nama", methods = ['POST'])
# def hello():
#     a ="YWRtaW46YWRtaW4xMjM="
#     b = a.encode("ascii") 
#     c = base64.b64decode(b)
#     d = c.decode("ascii")
#     e ="Z3Vlc3Q6Z3Vlc3Q0NTYg"
#     f = e.encode("ascii") 
#     g = base64.b64decode(f)
#     h = g.decode("ascii")
#     c = request.headers['Authorization']
#     ca = str(c)
#     base64_input = ca[6:].encode("ascii") 
#     input_bytes = base64.b64decode(base64_input)
#     inputa = input_bytes.decode("ascii")
#     if inputa != d and inputa != h:
#         abort(401)
#     elif inputa == d or inputa == h:
#         response = {"Message" : "Success!"}
#     return response
# @app.route("/library-fine", methods = ['POST'])
# def lib():
#         args = request.args
#         a = args.get("returned")
#         b = args.get("due")
#         d1 = int(a[8:])
#         m1 = int(a[5:7])
#         y1 = int(a[:4])
#         d2 = int(b[8:])
#         m2 = int(b[5:7])
#         y2 = int(b[:4])
#         # a = 0
#         if d1<=d2 and m1 <= m2  and y1 <=y2 or(d1==d2 and m1==m2 and y1<y2) or(d1!=d2 and m1!=m2 and y1<y2) or(d1>d2 and m1<m2 and y1==y2)or(d1>d2 and m1==m2 and y1<y2):
#           a = 0
#         elif d1>d2 and m1 == m2 and y1 ==y2:
#           a = abs(d1-d2) * 15
#         elif d1!=d2  and m1>m2 and y1==y2:
#           a = abs(m1-m2) * 500
#         elif d1!=d2 or d1 ==2 and m1!=m2 or m1==m2 and y1>y2:
#           a = 10000
#         return {"fine" : a,
#         }
# @app.route("/repeated-string/<s>" , methods = ['POST'])
# def subject(s):
#         n = request.headers['n']
#         x = int(n) // int(len(s))
#         y = int(n) % int(len(s))
#         a = str(str(s).count("a") * x + str(s[:y]).count("a"))
#         # return Response(headers={'Count': a})
#         resp = make_response('/repeated-string/<s>') #here you could use make_response(render_template(...)) too
#         resp.headers['Count'] = a
#         return resp

# @app.route("/",  methods = ['POST'])
# def hello_world():
#     k = request.get_json()
#     nums = k["items"]
#     counter = Counter(nums)
#     a = sorted(nums, key=lambda x: (counter[x], x))
#     b = [s for s in a if s.isdigit()]
#     return "items : " + str(nums) + "  sorted : " + str(b)



