#!/usr/bin/python
import datetime

class ScheduleParser():

  def get24HourBasedTime(self, text, col_num, num_of_cols):
    if text == '--':
      return None
    d = datetime.datetime.strptime(text, '%I:%M%p')
    t = int((d - datetime.datetime(1900, 1, 1)).total_seconds())
    # if time is before 4am then consider it the next morning
    if t < 4 * 3600:
      t += 24 * 3600
    return t

  def getTrainNumber(self, text):
    return text['data-trip-id']

  def generate_parse_schedule(self):
    def parse_schedule(soup, direction):

      table = soup.find('table', attrs={'data-direction': direction})
      table_rows = table.find('tbody').find_all('tr')

      cols = table_rows[0].find_all('td', attrs={'class': 'schedule-trip-header'})
      trains = [self.getTrainNumber(col) for col in cols]
      svctype = [col['data-service-type'] for col in cols]

      info = {'trains': trains, 'schedule': [], 'stations': [], 'service_type': svctype}
      for i, row in enumerate(table_rows[2:]):
        cells = [cell.text.strip() for cell in row.find_all(['th', 'td'])]
        if len(cells) == 1:
          continue

        info['stations'].append(cells[1])

        times = cells[2:]
        times = [self.get24HourBasedTime(time, ii, len(times)) for ii, time in enumerate(times)]

        info['schedule'].append({
          'zone': cells[0],
          'station': cells[1],
          'times': times,
        })

      return info
    return parse_schedule
