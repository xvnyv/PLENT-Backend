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
user_put_args.add_argument('id', type=str)

event_put_args = reqparse.RequestParser()
event_put_args.add_argument('title', type=str)
event_put_args.add_argument('date', type=list,  location='json')
event_put_args.add_argument('startTime', type=list, location='json')
event_put_args.add_argument('endTime', type=list, location='json')
event_put_args.add_argument('location', type=str)
event_put_args.add_argument('description', type=str)
event_put_args.add_argument('telegram', type=str)
event_put_args.add_argument('id', type=str)
event_put_args.add_argument('creatorId', type=str)
event_put_args.add_argument('type', type=str)
# event_put_args.add_argument('sign_up', type=bool)
event_put_args.add_argument('imageUrl', type=str)


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
        print(args)
        if len(list(mongo.db.event.find({'title': args['title'], 'date': args['date'], 'creatorId': args['creatorId']}))) == 0:
            args['attendees'] = []
            # args['startTime'] = 0 if args['startTime'] == None else int(args['startTime'])
            # args['endTime'] = 0 if args['endTime'] == None else int(args['endTime'])
            result = mongo.db.event.insert_one(args)
            
            print(str(result.inserted_id))
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
            print(user)
            print(event)
            for ev in mongo.db.event.find({'_id' : {'$in':user['events'], '$ne': event['_id']}}):
                if ev['date'] == event['date'] and (ev['startTime'] >= event['startTime'] and ev['startTime'] <= event['endTime']) or (ev['endTime'] >= event['startTime'] and ev['endTime'] <= event['endTime']):
                    event['clashString'] = f'You have "{ev["title"]}" at {ev["startTime"]} on {ev["date"]}'
                    break

            del event['_id']

        print(event)
        return event

class Events(Resource):
    def get(self):
        upcoming_events = []
        current_date = datetime.datetime.today()
        for event in mongo.db.event.find({}):
            event_date = datetime.datetime(event['date'][2], event['date'][1], event['date'][0])
            event_date = event_date.replace(hour=event['startTime'][0], minute=event['startTime'][1])
            event['id'] = str(event['_id'])
            del event['_id']
            if event_date >= current_date: 
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
    app.run(debug=True)