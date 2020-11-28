import os
import pytz
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
user_put_args.add_argument('id', type=str)

event_put_args = reqparse.RequestParser()
event_put_args.add_argument('title', type=str)
event_put_args.add_argument('date', type=str)
event_put_args.add_argument('startTime', type=str)
event_put_args.add_argument('endTime', type=str)
event_put_args.add_argument('location', type=str)
event_put_args.add_argument('description', type=str)
event_put_args.add_argument('telegram', type=str)
event_put_args.add_argument('id', type=str)
event_put_args.add_argument('creatorId', type=str)
event_put_args.add_argument('type', type=str)
event_put_args.add_argument('imageUrl', type=str)

event_user_put_args = reqparse.RequestParser()
event_user_put_args.add_argument('event_id', type=str)
event_user_put_args.add_argument('user_id', type=str)
event_user_put_args.add_argument('sign_up', type=bool)

def pad_zero(digit):
    return '0' if len(digit) == 1 else ''

class User(Resource):
    def post(self):
        args = user_put_args.parse_args()
        if len(list(mongo.db.user.find({'studentId': args['studentId']}))) == 0:
            result = mongo.db.user.insert_one(args)
            print(result.inserted_id)

            return {'id': str(result.inserted_id), 'permission': 0}

    # def put(self):
    #     args = user_put_args.parse_args()
    #     user = mongo.db.user.find({'_id': ObjectId(args['id'])})
    #     if user != None:
    #         user['name'] = args['name']
    #         user['student']

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
        args['date'] = [int(d) for d in args['date'].split('-')[::-1]]
        args['startTime'] = [int(st) for st in args['startTime'].split(':')]
        args['endTime'] = [int(et) for et in args['endTime'].split(':')]
        if len(list(mongo.db.event.find({'title': args['title'], 'date': args['date'], 'creatorId': args['creatorId']}))) == 0:
            args['attendees'] = []
            result = mongo.db.event.insert_one(args)
            
            print(str(result.inserted_id))
            return {'id': str(result.inserted_id)}

    def put(self):
        args = event_user_put_args.parse_args()
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
            print(user)
            print(event)
            for ev in mongo.db.event.find({'_id' : {'$in':user['events'], '$ne': event['_id']}}):
                if ev['date'] == event['date'] and (ev['startTime'] >= event['startTime'] and ev['startTime'] <= event['endTime']) or (ev['endTime'] >= event['startTime'] and ev['endTime'] <= event['endTime']):
                    event['clashString'] = f'You have "{ev["title"]}" at {ev["startTime"]} on {ev["date"]}'
                    break

            del event['_id']
            event['date'] = str(event['date'][2]) + '-' + pad_zero(str(event['date'][1])) + str(event['date'][1]) + '-' + pad_zero(str(event['date'][0])) + str(event['date'][0])
            event['startTime'] = pad_zero(str(event['startTime'][0])) + str(event['startTime'][0]) + ':' + pad_zero(str(event['startTime'][1])) + str(event['startTime'][1])
            event['endTime'] = pad_zero(str(event['endTime'][0])) + str(event['endTime'][0]) + ':' + pad_zero(str(event['endTime'][1])) + str(event['endTime'][1])

        print(event)
        return event

class Events(Resource):
    def get(self):
        upcoming_events = []
        current_date = datetime.datetime.now(pytz.timezone('Asia/Singapore'))
        for event in mongo.db.event.find({}, {'_id': 1, 'imageUrl': 1, 'title': 1, 'date': 1, 'startTime': 1, 'endTime': 1, 'type': 1}):
            event_date = datetime.datetime(event['date'][2], event['date'][1], event['date'][0], event['startTime'][0], event['startTime'][1])
            event_date = event_date.astimezone(pytz.timezone('Asia/Singapore'))
            event['id'] = str(event['_id'])
            del event['_id']
            if event_date >= current_date: 
                event['date'] = str(event['date'][2]) + '-' + pad_zero(str(event['date'][1])) + str(event['date'][1]) + '-' + pad_zero(str(event['date'][0])) + str(event['date'][0])
                event['startTime'] = pad_zero(str(event['startTime'][0])) + str(event['startTime'][0]) + ':' + pad_zero(str(event['startTime'][1])) + str(event['startTime'][1])
                event['endTime'] = pad_zero(str(event['endTime'][0])) + str(event['endTime'][0]) + ':' + pad_zero(str(event['endTime'][1])) + str(event['endTime'][1])
                upcoming_events.append(event)

        return upcoming_events

class Calendar(Resource):
    def get(self):
        user_id = request.args.get("user_id")
        date = request.args.get("date")

        user = mongo.db.user.findOne({'_id': ObjectId(user_id)})
        events = []

        for ev in mongo.db.event.find({'_id': {'$in': user['events']}, 'date': [int(date[:2]), int(date[2:4]), int(date[4:])]}):
            ev['id'] = str(ev['_id'])
            del ev['_id']

            events.append(ev)

        return events

class Organised(Resource):
    def get(self):
        # add new field for plannedEvents or sth like that so that you can distinguish between events user is attending vs events users are organising
        pass

class Participants(Resource):
    def get(self):
        event_id = request.args.get("event_id")
        event = mongo.db.event.findOne({"_id": ObjectId(event_id)})

        users = []

        for usr in mongo.db.user.find({'_id': {'$in': event['attendees']}}):
            usr['id'] = str(usr['_id'])
            del usr['_id']

            users.append(usr)

        return users

api.add_resource(User, '/user')
api.add_resource(Event, '/event')
api.add_resource(Events, '/events')
api.add_resource(Calendar, '/calendar')
api.add_resource(Organised, '/organised')
api.add_resource(Participants, '/participants')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)