#!/usr/bin/python
from bs4 import BeautifulSoup
import os, urllib2, json
import sys, argparse
from generate_parse_schedule import ScheduleParser

class CaltrainScraper():

  def __init__(self):
    parser = argparse.ArgumentParser(description = "Scrapes the Caltrain website")
    parser.add_argument('-c', '--clear', action='store_true', help="Clear the current cache of HTML files")
    args = parser.parse_args(sys.argv[1:])

    schedule_parser = ScheduleParser()
    self.parse_weekday_schedule = schedule_parser.generate_parse_schedule()
    #self.parse_saturday_schedule = schedule_parser.generate_parse_schedule(3, 0, 'saturday', geolocations)
    #self.parse_sunday_schedule = schedule_parser.generate_parse_schedule(3, 0, 'sunday', geolocations)

    urls = {
      #'saturday': 'http://www.caltrain.com/schedules/weekend-timetable.html',
      'weekday': 'https://www.caltrain.com/?active_tab=route_explorer_tab',
      #'sunday': 'http://www.caltrain.com/schedules/weekend-timetable.html',
    }

    if args.clear: self.clear_cache(urls)

    for key, url in urls.iteritems():
      schedule = self.get_schedule(
        url,
        key,
      )

    self.save_to_json(schedule, 'schedule')

  def get_location(self, name, file_extension):
    parent_path = os.path.abspath(os.curdir)
    file_name = "%s/%s/%s.%s" % ('data', file_extension, name, file_extension)
    return os.path.join(parent_path, file_name)

  def get_schedule(self, schedule_url, schedule_name, **kwargs):

    html = open(self.get_location(schedule_name, 'html'), 'r')
    soup = BeautifulSoup(html, features="html.parser")
    directions = ['northbound', 'southbound']
    schedule = {}
    for dir in directions:
      if schedule_name is 'weekday':
        schedule[dir] = self.parse_weekday_schedule(soup, dir)
      elif schedule_name is 'saturday':
        train_times, station_times = self.parse_saturday_schedule(
          soup,
          value,
          train_times=train_times,
          station_times=station_times,
        )
      elif schedule_name is 'sunday':
        train_times, station_times = self.parse_sunday_schedule(
          soup,
          value,
          train_times=train_times,
          station_times=station_times,
        )
    return schedule

  def clear_cache(self, urls):
    print('Clear Cache')
    for name, url in urls.iteritems():
      print('Get URL', url)
      try:
        html = urllib2.urlopen(url).read()
        html_file = open(self.get_location(name, 'html'), 'w')
        html_file.write(html)
        html_file.close()
      except Exception as e:
        print('Error', e)

  def save_to_json(self, data, name):
    print("Saving To: %s" % self.get_location(name, 'json'))
    json_file = open(self.get_location(name, 'json'), 'w')
    json_file.write(json.dumps(data, indent=2, separators=(',', ': ')))
    json_file.close()

if __name__ == "__main__":
  CaltrainScraper()
