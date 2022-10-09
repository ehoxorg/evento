from asyncio import events
from flask import Flask, jsonify, request, abort
from flask_restful import Resource, Api
from datetime import datetime
from marshmallow import Schema, fields
import pytz
import xmltodict
import requests
import pprint
import sys

app = Flask(__name__)
api = Api(app)

utc = pytz.UTC
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
PROVIDER_ENDPOINT_URL = "https://provider.code-challenge.feverup.com/api/events"
pp = pprint.PrettyPrinter(indent=2)


class EventQuerySchema(Schema):
    starts_at = fields.DateTime(required=True, error_messages={
                                "required": "starts_at is required."})
    ends_at = fields.DateTime(required=True, error_messages={
                              "required": "ends_at is required."})


schema = EventQuerySchema()


class EventApi(Resource):
    def get(self):
        args = request.args
        errors = schema.validate(args)
        if errors:
            abort(400, str(errors))
        argsLoad = schema.load(args)
        isStartsAtTzNotAware = argsLoad.get("starts_at").tzinfo is None or argsLoad.get("starts_at").tzinfo.utcoffset(argsLoad.get("starts_at")) is None
        isEndsAtTzNotAware = argsLoad.get("ends_at").tzinfo is None or argsLoad.get("ends_at").tzinfo.utcoffset(argsLoad.get("ends_at")) is None
        if isStartsAtTzNotAware:
            abort(400, str({'error': 'starts_at parameter needs to be in UTC', 'example': '2021-06-29T14:32:28Z'}))
        if isEndsAtTzNotAware:
            abort(400, str({'error': 'ends_at parameter needs to be in UTC', 'example': '2021-06-29T14:32:28Z'}))
        onlineRemoteEvents = getRemoteEventsAndFilterOnline()
        pp.pprint(onlineRemoteEvents)
        remoteEventsWithinRange = filterByDates(argsLoad.get("starts_at"), argsLoad.get("ends_at"), onlineRemoteEvents)
        eventDtoList = convertToEventDtoList(remoteEventsWithinRange)
        return jsonify({
                    "data": {
                        "events":eventDtoList
                    }
                })

def getRemoteEventsAndFilterOnline():
    r = requests.get(url=PROVIDER_ENDPOINT_URL)
    responseBodyDict = xmltodict.parse(r.content)
    baseEventList = responseBodyDict['eventList']['output']['base_event']
    onlineEvents = [v for v in baseEventList if v['@sell_mode'] == 'online']
    return onlineEvents


def convertToEventDtoList(remoteEvents):
    eventDtoList = []
    for v in remoteEvents:
        eventDtoList.append(convertToSingleEventDto(v))
    return eventDtoList


def convertToSingleEventDto(remoteEvent):
    eventDto = {}
    eventDto['id'] = remoteEvent['@base_event_id']
    eventDto['title'] = remoteEvent['@title']
    startDateObj = deserializeDatetime(remoteEvent['event']['@event_start_date'])
    eventDto['start_date'] = str(startDateObj.date())
    eventDto['start_time'] = startDateObj.strftime("%H:%M:%S")
    endDateObj = deserializeDatetime(remoteEvent['event']['@event_end_date'])
    eventDto['end_date'] = str(endDateObj.date())
    eventDto['end_time'] = endDateObj.strftime("%H:%M:%S")
    eventDto['min_price'], eventDto['max_price'] = extractMinAndMaxPrice(remoteEvent['event']['zone'])
    return eventDto

def extractMinAndMaxPrice(zone):
    minPrice = sys.float_info.max
    maxPrice = sys.float_info.min
    if type(zone) == list:
        for z in zone:
            minPrice = min(float(z['@price']), minPrice)
            maxPrice = max(float(z['@price']), maxPrice)
    else: 
        minPrice = min(float(zone['@price']), minPrice)
        maxPrice = max(float(zone['@price']), maxPrice)
    return minPrice, maxPrice

def filterByDates(startAtQueryParam: datetime, endAtQueryParam: datetime, remoteEvents: list):
    filtered = []
    for e in remoteEvents:
        isEventStartTimeAfter = deserializeDatetime(
            e['event']["@event_start_date"]) >= startAtQueryParam
        isEventEndTimeBefore = deserializeDatetime(
            e['event']["@event_end_date"]) <= endAtQueryParam
        if isEventStartTimeAfter & isEventEndTimeBefore:
            filtered.append(e)
    return filtered


def deserializeDatetime(dateTimeStr):
    return utc.localize(datetime.strptime(dateTimeStr, DATE_TIME_FORMAT))


api.add_resource(EventApi, '/search')

if __name__ == '__main__':
    app.run(debug=True)
