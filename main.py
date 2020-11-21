import os
import datetime

from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config["MONGO_URI"] = os.getenv('MONGODB_CONNECTION_STRING')
app.config["MONGO_DBNAME"] = 'plent'

mongo = PyMongo(app)

user_put_args = reqparse.RequestParser()
user_put_args.add_argument('name', type=str)
user_put_args.add_argument('email', type=str)
user_put_args.add_argument('studentId', type=str)
user_put_args.add_argument('password', type=str)

event_put_args = reqparse.RequestParser()
event_put_args.add_argument('title', type=str)
event_put_args.add_argument('date', type=str)
event_put_args.add_argument('start_time', type=str)
event_put_args.add_argument('end_time', type=str)
event_put_args.add_argument('location', type=str)
event_put_args.add_argument('description', type=str)
event_put_args.add_argument('telegram', type=str)
event_put_args.add_argument('event_id', type=str)
event_put_args.add_argument('user_id', type=str)
event_put_args.add_argument('sign_up', type=bool)


class User(Resource):
    def post(self):
        args = user_put_args.parse_args()
        if len(list(mongo.db.user.find({'studentId': args['studentId']}))) == 0:
            result = mongo.db.user.insert_one(args)
            print(result.inserted_id)

            return {'id': str(result.inserted_id), 'permission': 0}

    def get(self):
        email = request.args.get('email')
        user = mongo.db.user.find_one({'email': email})
        if user != None:
            user['id'] = str(user['_id'])
            del user['_id']

            user['events'] = [str(e) for e in user['events']]

        return user


class Event(Resource):
    def post(self):
        args = event_put_args.parse_args()
        if len(list(mongo.db.event.find({'title': args['title'], 'date': args['date']}))) == 0:
            args['attendees'] = []
            del args['clashString']
            args['start_time'] = int(args['start_time'])
            args['end_time'] = int(args['end_time'])
            result = mongo.db.event.insert_one(args)
            
            return {'id': str(result.inserted_id)}

    def put(self):
        args = event_put_args.parse_args()
        operation = "$pull"
        if args['sign_up']:
            operation = "$addToSet"
        
        mongo.db.user.update_one({'_id': ObjectId(args['user_id'])}, {operation: {'events': ObjectId(args['event_id'])}})
        mongo.db.event.update_one({'_id': ObjectId(args['event_id'])}, {operation: {'attendees': ObjectId(args['user_id'])}})
        
        print(args['event_id'])
        print(args['user_id'])

        return {'success': True}

    def get(self):
        event_id = request.args.get('event_id')
        user_id = request.args.get('user_id')
        event = mongo.db.event.find_one({'_id': ObjectId(event_id)})
        if event != None:
            event['id'] = str(event['_id'])
            event['attendees'] = [str(a) for a in event['attendees']]
            

            event['clashString'] = ''
            user = mongo.db.user.find_one({'_id': ObjectId(user_id)})
            
            for ev in mongo.db.event.find({'_id' : {'$in':user['events'], '$ne': event['_id']}}):
                if ev['date'] == event['date'] and (ev['start_time'] >= event['start_time'] and ev['start_time'] <= event['end_time']) or (ev['end_time'] >= event['start_time'] and ev['end_time'] <= event['end_time']):
                    event['clashString'] = f'You have "{ev["title"]}" at {ev["start_time"]} on {ev["date"]}'
                    break

            del event['_id']

        print(event)
        return event

api.add_resource(User, '/user')
api.add_resource(Event, '/event')


if __name__ == "__main__":
    app.run(debug=True)