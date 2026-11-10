"""Build hourly and daily summaries independently with SQLite and pandas."""
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .db import connect, day
from .prepare_data import validate
from .sample import END, EXPECTED, START

BASE = """
WITH RECURSIVE calendar(hour_start) AS (
    SELECT :first_hour
    UNION ALL
    SELECT datetime(hour_start, '+1 hour') FROM calendar
    WHERE datetime(hour_start, '+1 hour') < :stop
), grid AS (
    SELECT r.room_id, r.name AS room, c.hour_start,
           date(c.hour_start) AS day,
           (CAST(strftime('%w',c.hour_start) AS INTEGER)+6)%7 AS weekday,
           CAST(strftime('%H',c.hour_start) AS INTEGER) AS hour,
           o.wh
    FROM calendar c CROSS JOIN rooms r
    LEFT JOIN readings o USING (room_id, hour_start)
), totals AS (
    SELECT room_id,room,day,COUNT(*) AS expected_hours,COUNT(wh) AS measured_hours,
           SUM(wh) AS recorded_wh
    FROM grid GROUP BY room_id,room,day
), shared_days AS (
    SELECT day FROM totals GROUP BY day HAVING MIN(measured_hours)=24 AND COUNT(*)=3
), daily AS (
    SELECT t.*,expected_hours-measured_hours AS missing_hours,
           measured_hours*100.0/expected_hours AS coverage_pct,
           CASE WHEN measured_hours=24 THEN recorded_wh END AS full_day_wh,
           CAST(s.day IS NOT NULL AS INTEGER) AS common_day
    FROM totals t LEFT JOIN shared_days s USING(day)
)
"""

QUERIES = {
    'hourly': BASE + 'SELECT * FROM grid',
    'daily': BASE + """
        SELECT *, CASE WHEN full_day_wh IS NOT NULL THEN
            DENSE_RANK() OVER (PARTITION BY room_id ORDER BY full_day_wh DESC)
        END AS day_rank
        FROM daily
    """,
    'room_comparison': BASE + """
        SELECT r.room_id,r.name AS room,COUNT(d.day) AS common_days,
               SUM(d.full_day_wh) AS total_wh
        FROM rooms r LEFT JOIN daily d ON d.room_id=r.room_id AND d.common_day=1
        GROUP BY r.room_id,r.name
    """,
    'weekday_hour': BASE + """
        , weekdays(weekday) AS (SELECT 0 UNION ALL SELECT weekday+1 FROM weekdays WHERE weekday<6),
        hours(hour) AS (SELECT 0 UNION ALL SELECT hour+1 FROM hours WHERE hour<23),
        grouped AS (
            SELECT room_id,weekday,hour,COUNT(*) AS expected_hours,
                   COUNT(wh) AS measured_hours,AVG(wh) AS mean_wh
            FROM grid GROUP BY room_id,weekday,hour
        )
        SELECT r.room_id,r.name AS room,w.weekday,h.hour,
               COALESCE(g.expected_hours,0) AS expected_hours,
               COALESCE(g.measured_hours,0) AS measured_hours,g.mean_wh
        FROM rooms r CROSS JOIN weekdays w CROSS JOIN hours h
        LEFT JOIN grouped g ON g.room_id=r.room_id AND g.weekday=w.weekday AND g.hour=h.hour
    """,
    'whole_house_hours': BASE + """
        , complete AS (
            SELECT hour_start,SUM(wh) AS total_wh
            FROM grid GROUP BY hour_start HAVING COUNT(wh)=3
        )
        SELECT hour_start,total_wh,DENSE_RANK() OVER (ORDER BY total_wh DESC) AS peak_rank
        FROM complete
    """,
}

SORT_KEYS = {
    'hourly': ['hour_start','room_id'],
    'daily': ['day','room_id'],
    'room_comparison': ['room_id'],
    'weekday_hour': ['room_id','weekday','hour'],
    'whole_house_hours': ['peak_rank','hour_start'],
    'quality': ['metric'],
}


def period(start=START, end=END):
    day(start)
    day(end)
    if not START <= start <= end <= END:
        raise ValueError('Chọn khoảng ngày hợp lệ trong tháng 4/2026')
    next_day = date.fromisoformat(end) + timedelta(days=1)
    return {'first_hour': start+' 00:00:00', 'stop': str(next_day)+' 00:00:00'}


def sql_tables(db, start=START, end=END):
    params = period(start, end)
    with connect(db) as connection:
        return {
            name: pd.read_sql_query(query, connection, params=params).sort_values(SORT_KEYS[name])
            for name, query in QUERIES.items()
        }


def pandas_tables(db, start=START, end=END):
    params = period(start, end)
    with connect(db) as connection:
        rooms = pd.read_sql_query('SELECT room_id,name AS room FROM rooms', connection)
        source = pd.read_sql_query('SELECT room_id,hour_start,wh FROM readings', connection)
    dates = pd.date_range(params['first_hour'], params['stop'], freq='h', inclusive='left')
    calendar = pd.DataFrame({'hour_start': dates.strftime('%Y-%m-%d %H:%M:%S'),
                             'day': dates.strftime('%Y-%m-%d'),
                             'weekday': dates.dayofweek, 'hour': dates.hour})
    grid = calendar.merge(rooms, how='cross').merge(source, on=['room_id','hour_start'], how='left')
    daily = grid.groupby(['room_id','room','day'], as_index=False).agg(
        expected_hours=('wh','size'), measured_hours=('wh','count'),
        recorded_wh=('wh',lambda v: v.sum(min_count=1)))
    daily['missing_hours'] = daily.expected_hours - daily.measured_hours
    daily['coverage_pct'] = daily.measured_hours * 100 / daily.expected_hours
    daily['full_day_wh'] = daily.recorded_wh.where(daily.measured_hours == 24)
    daily['common_day'] = daily.groupby('day').measured_hours.transform('min').eq(24).astype(int)
    daily['day_rank'] = daily.groupby('room_id').full_day_wh.rank(method='dense', ascending=False)

    common = daily[daily.common_day == 1].groupby('room_id', as_index=False).agg(
        common_days=('day','size'), total_wh=('full_day_wh','sum'))
    comparison = rooms.merge(common,on='room_id',how='left')
    comparison['common_days'] = comparison.common_days.fillna(0).astype(int)

    summary = grid.groupby(['room_id','weekday','hour'], as_index=False).agg(
        expected_hours=('wh','size'), measured_hours=('wh','count'), mean_wh=('wh','mean'))
    axes = pd.MultiIndex.from_product([rooms.room_id,range(7),range(24)],
                                      names=['room_id','weekday','hour']).to_frame(index=False)
    summary = axes.merge(rooms,on='room_id').merge(summary,on=['room_id','weekday','hour'],how='left')
    for column in ['expected_hours','measured_hours']:
        summary[column] = summary[column].fillna(0).astype(int)

    by_hour = grid.groupby('hour_start').wh
    complete = by_hour.sum(min_count=3).dropna().rename('total_wh').reset_index()
    complete['peak_rank'] = complete.total_wh.rank(method='dense',ascending=False)

    quality = pd.DataFrame([
        ('expected_hours', EXPECTED), ('measured_hours',len(source)),
        ('missing_hours',EXPECTED-len(source)), ('zero_readings',int(source.wh.eq(0).sum()))
    ],columns=['metric','value'])
    return dict(hourly=grid,daily=daily,room_comparison=comparison,weekday_hour=summary,
                whole_house_hours=complete,quality=quality)


def compare(db, start=START, end=END):
    quality = validate(db)
    sql = dict(sql_tables(db,start,end), quality=quality)
    pandas = pandas_tables(db,start,end)
    for name, actual in sql.items():
        keys = SORT_KEYS[name]
        actual = actual.sort_values(keys).reset_index(drop=True)
        expected = pandas[name][actual.columns].sort_values(keys).reset_index(drop=True)
        if len(actual) != len(expected):
            raise ValueError(f'SQL và pandas khác số dòng tại {name}')
        for column in actual:
            a, b = actual[column], expected[column]
            if column in ('coverage_pct','mean_wh'):
                match = np.allclose(a.astype(float),b.astype(float),atol=1e-8,rtol=0,equal_nan=True)
            else:
                match = ((a == b) | (a.isna() & b.isna())).all()
            if not match:
                raise ValueError(f'SQL và pandas khác nhau tại {name}.{column}')
        sql[name] = actual
    return sql
