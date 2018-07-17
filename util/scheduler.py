"""
Scheduler module by Sierra

---------------------------------------------------------------------------
The MIT License (MIT)

Copyright (c) 2018 CantSayIHave

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
---------------------------------------------------------------------------

Used to schedule functions based on datetimes. The smallest time event is
the hour.

"""

from datetime import datetime
import asyncio
import traceback
import sys

from . import global_util


events = []


class TimeEvent:
    def __init__(self, dt: datetime, callback, delete=True):
        self.dt = dt
        self.callback = callback
        self.delete = delete

    def __str__(self):
        return 'TimeEvent:[dt={},cb={}]'.format(self.dt.strftime(global_util.DATETIME_FORMAT), self.callback)

    def __repr__(self):
        return str(self)


class HourEvent(TimeEvent):

    def __eq__(self, other):
        if not isinstance(other, (TimeEvent, datetime)):
            raise ValueError('Expected a `TimeEvent` or `datetime` to compare to')

        if isinstance(other, TimeEvent):
            return self.dt.hour == other.dt.hour
        elif isinstance(other, datetime):
            return self.dt.hour == other.hour


class DayEvent(TimeEvent):

    def __eq__(self, other):
        if not isinstance(other, (TimeEvent, datetime)):
            raise ValueError('Expected a `TimeEvent` or `datetime` to compare to')

        if isinstance(other, TimeEvent):
            return self.dt.day == other.dt.day
        elif isinstance(other, datetime):
            return self.dt.day == other.day


class YearEvent(TimeEvent):

    def __eq__(self, other):
        if not isinstance(other, (TimeEvent, datetime)):
            raise ValueError('Expected a `TimeEvent` or `datetime` to compare to')

        if isinstance(other, TimeEvent):
            return self.dt.year == other.dt.year
        elif isinstance(other, datetime):
            return self.dt.year == other.year


class AbsoluteDateEvent(TimeEvent):

    def __eq__(self, other):
        if not isinstance(other, (TimeEvent, datetime)):
            raise ValueError('Expected a `TimeEvent` or `datetime` to compare to')

        if isinstance(other, TimeEvent):
            return self.dt.date() == other.dt.date()
        elif isinstance(other, datetime):
            return self.dt.date() == other.date()


class RelativeDateEvent(TimeEvent):

    def __eq__(self, other):
        if not isinstance(other, (TimeEvent, datetime)):
            raise ValueError('Expected a `TimeEvent` or `datetime` to compare to')

        if isinstance(other, TimeEvent):
            return self.dt.day == other.dt.day and self.dt.month == other.dt.month
        elif isinstance(other, datetime):
            return self.dt.day == other.day and self.dt.month == other.month


def register_event(dt: datetime, cb, delete, baseclass):
    if not issubclass(baseclass, TimeEvent):
        raise ValueError('Must register a `TimeEvent` subclass')

    events.append(baseclass(dt=dt, callback=cb, delete=delete))


def register_hour_event(hour, callback, delete=True):
    now = datetime.now()
    register_event(now.replace(hour=hour), callback, delete, HourEvent)


def register_day_event(day, callback, delete=True):
    now = datetime.now()
    register_event(now.replace(day=day), callback, delete, DayEvent)


# todo: the rest of the events etc


def execute(loop=None):
    now = datetime.now()
    for event in events:  # type: TimeEvent
        if event == now:
            if asyncio.iscoroutinefunction(event.callback):
                loop.create_task(event.callback())
            else:
                event.callback()

            if event.delete:
                events.remove(event)


# handles the exceptions, so preferred
async def async_execute():
    now = datetime.now()
    for event in events:
        if event == now:
            try:
                if asyncio.iscoroutinefunction(event.callback):
                    await event.callback()
                else:
                    event.callback()
            except Exception as e:
                print('Ignoring scheduler exception {}:'.format(e.__class__.__name__))
                traceback.print_exc(file=sys.stdout)

            if event.delete:
                events.remove(event)


async def task_loop(delay=60):
    """A default 'loop' for watching and running events

    Overriding this or writing your own requires calling
    one of the execute functions

    Checks every minute for an hour change event
    """
    while True:
        prev = datetime.now()
        await asyncio.sleep(delay)
        if prev.hour != datetime.now().hour:
            await async_execute()
