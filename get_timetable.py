import requests
import datetime
import functools
import json

APIKEY = 'APIKEY'
OPERATOR = 'CT'
APIURL = 'https://api.511.org/transit'

class Line:
  def __init__(self, obj):
    self.line = obj

  def __repr__(self):
    return self.line['Id']

  @classmethod
  def getAll(cls):
    res = requests.get('{}/lines'.format(APIURL), params={'api_key': APIKEY, 'operator_id': OPERATOR, 'format': 'json'})
    js = json.loads(res.text.encode().decode('utf-8-sig'))
    return [Line(x) for x in js]


class StopPlace:
  def __init__(self, obj):
    self.stopPlace = obj

  def __repr__(self):
    return self.stopPlace['@id']

  @classmethod
  def getAll(cls):
    res = requests.get('{}/stopPlaces'.format(APIURL), params={'api_key': APIKEY, 'operator_id': OPERATOR, 'format': 'json'})
    js = json.loads(res.text.encode().decode('utf-8-sig'))
    return [StopPlace(x) for x in js['Siri']['ServiceDelivery']['DataObjectDelivery']['dataObjects']['SiteFrame']['stopPlaces']['StopPlace']]

  @classmethod
  def filter(self, stops, calls):
    stopIds = [c.stopId() for c in calls]
    return [x for x in stops if x.stopPlace['@id'] in stopIds]

  def name(self):
    name = self.stopPlace['Name']
    if name.endswith(' Caltrain Station'):
      name = name[0:-17]
    return name


class Timetable:
  def __init__(self, obj):
    self.timetable = obj

  @classmethod
  def get(cls, line):
    res = requests.get('{}/timetable'.format(APIURL), params={'api_key': APIKEY, 'operator_id': OPERATOR, 'line_id': line, 'format': 'json'})
    js = json.loads(res.text.encode().decode('utf-8-sig'))
    return Timetable(js)

  def serviceJourneys(self, direction):
    if not 'TimetableFrame' in self.timetable['Content']:
      return []
    out = []
    for frame in self.timetable['Content']['TimetableFrame']:
      for sj in frame['vehicleJourneys']['ServiceJourney']:
        if sj['JourneyPatternView']['DirectionRef']['ref'].startswith(direction):
          out.append(ServiceJourney(sj))
    return out


class ServiceJourney:
  def __init__(self, obj):
    self.serviceJourney = obj

  def __eq__(self, a):
    return self.calls()[0].departure() == a.calls()[0].departure()

  def __lt__(self, a):
    return self.calls()[0].departure() < a.calls()[0].departure()

  def __contains__(self, a):
    return self.order(a) != -1

  def id(self):
    return self.serviceJourney['id']

  def direction(self):
    return self.serviceJourney['JourneyPatternView']['DirectionRef']['ref']

  def calls(self):
    return [Call(x, self) for x in self.serviceJourney['calls']['Call']]

  def call(self, stop):
    for c in self.calls():
      if c.stopId() == str(stop):
        return c
    return None

  def order(self, stop):
    c = self.call(stop)
    return c.order() if c else -1


class Call:
  def __init__(self, call, sj):
    self.call = call
    self.sj = sj

  def __repr__(self):
    return '{} {} {} {}'.format(self.sj.id(), self.sj.direction(), self.call['ScheduledStopPointRef']['ref'], self.call['Departure']['Time'])

  def stopId(self):
    return self.call['ScheduledStopPointRef']['ref']

  def order(self):
    return int(self.call['order'])

  def departure(self):
    return ft(self.call['Departure']['Time'])


def sort_stops(a, b, journeys):
  for j in journeys:
    ai = j.order(a)
    bi = j.order(b)
    if ai != -1 and bi != -1:
      if ai == bi:
        continue
      if ai > bi:
        return 1
      return -1
  return 0

def ft(text):
  d = datetime.datetime.strptime(text, '%H:%M:%S')
  t = int((d - datetime.datetime(1900, 1, 1)).total_seconds())
  # if time is before 4am then consider it the next morning
  if t < 4 * 3600:
    t += 24 * 3600
  return t

def directionData(alltimetables, allstops, dirchar):
  nbCalls = []
  nbJourneys = []
  for tt in alltimetables:
    for sj in tt.serviceJourneys(dirchar):
      nbJourneys.append(sj)
      nbCalls.extend(sj.calls())

  sortedJourneys = sorted(nbJourneys)
  sortedStops = sorted(StopPlace.filter(allstops, nbCalls), key=functools.cmp_to_key(lambda a,b: sort_stops(a, b, nbJourneys)))
  return sortedJourneys, sortedStops

def direction(alltimetables, allstops, dirchar):
  sortedJourneys, sortedStops = directionData(alltimetables, allstops, dirchar)
  schedule = []
  for stop in sortedStops:
    station = {'station': stop.name(), 'times': []}
    stype = []
    trains = []

    for sj in sortedJourneys:
      c = sj.call(stop)
      station['times'].append(c.departure() if c else None)
      stype.append('weekday')
      trains.append(sj.id())

    schedule.append(station)
  return {'service_type': stype, 'stations': [s.name() for s in sortedStops], 'trains': trains, 'schedule': schedule}


stops = StopPlace.getAll()
timetables = []
for line in Line.getAll():
  timetables.append(Timetable.get(line))

out = {}
out['northbound'] = direction(timetables, stops, 'N')
out['southbound'] = direction(timetables, stops, 'S')
print(json.dumps(out, indent=4))
