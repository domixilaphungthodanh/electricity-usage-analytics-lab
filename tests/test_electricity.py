import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from electricity_lab.analysis import compare, period, sql_tables
from electricity_lab.analyze import export
from electricity_lab.db import connect
from electricity_lab.prepare_data import create, prepare
from electricity_lab.sample import generate


class ElectricityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.db = self.root / 'electricity.db'
        create(self.db)

    def test_full_calendar_and_source_counts(self):
        tables = compare(self.db)
        self.assertEqual(len(tables['hourly']),2160)
        self.assertEqual(len(tables['daily']),90)
        self.assertEqual(len(tables['weekday_hour']),504)
        self.assertEqual(tables['quality'].set_index('metric').value.to_dict(),
                         {'expected_hours':2160,'measured_hours':2084,
                          'missing_hours':76,'zero_readings':78})

    def test_zero_is_measured(self):
        rows = compare(self.db,'2026-04-01','2026-04-01')
        zero = rows['hourly'].query('room_id==1 and hour==0').iloc[0]
        living = rows['daily'].query('room_id==1').iloc[0]
        self.assertEqual(zero.wh,0)
        self.assertEqual(living.measured_hours,24)
        self.assertEqual(living.coverage_pct,100)

    def test_partial_day(self):
        rows = compare(self.db,'2026-04-01','2026-04-01')
        work = rows['daily'].query('room_id==3').iloc[0]
        self.assertEqual(work.measured_hours,20)
        self.assertEqual(work.missing_hours,4)
        self.assertAlmostEqual(work.coverage_pct,100*20/24)
        self.assertGreater(work.recorded_wh,0)
        self.assertTrue(pd.isna(work.full_day_wh))
        self.assertTrue(pd.isna(work.day_rank))

    def test_entire_room_day_missing(self):
        tables = compare(self.db,'2026-04-02','2026-04-02')
        bedroom = tables['daily'].query('room_id==2').iloc[0]
        self.assertEqual(bedroom.coverage_pct,0)
        self.assertTrue(pd.isna(bedroom.recorded_wh))
        self.assertTrue(pd.isna(bedroom.full_day_wh))
        self.assertTrue(tables['whole_house_hours'].empty)

    def test_common_days_are_identical(self):
        tables = compare(self.db,'2026-04-01','2026-04-03')
        daily = tables['daily'].query('common_day==1')
        self.assertEqual(daily.day.unique().tolist(),['2026-04-03'])
        self.assertEqual(tables['room_comparison'].common_days.tolist(),[1,1,1])
        self.assertEqual(tables['room_comparison'].total_wh.tolist(),
                         daily.sort_values('room_id').full_day_wh.tolist())

    def test_no_common_days(self):
        comparison = compare(self.db,'2026-04-01','2026-04-02')['room_comparison']
        self.assertTrue(comparison.common_days.eq(0).all())
        self.assertTrue(comparison.total_wh.isna().all())

    def test_peak_excludes_incomplete_hour(self):
        with connect(self.db,False) as connection:
            connection.execute("""
                UPDATE readings SET wh=1000000000
                WHERE room_id=1 AND hour_start='2026-04-01 08:00:00'
            """)
        peaks = compare(self.db,'2026-04-01','2026-04-01')['whole_house_hours']
        self.assertEqual(len(peaks),20)
        self.assertNotIn('2026-04-01 08:00:00',peaks.hour_start.tolist())
        self.assertLess(peaks.total_wh.max(),1000000000)

    def test_zero_totals_and_tied_peaks(self):
        with connect(self.db,False) as connection:
            connection.execute("UPDATE readings SET wh=0 WHERE hour_start LIKE '2026-04-03%'")
        tables = compare(self.db,'2026-04-03','2026-04-03')
        peaks = tables['whole_house_hours']
        self.assertEqual(len(peaks),24)
        self.assertTrue(peaks.total_wh.eq(0).all())
        self.assertTrue(peaks.peak_rank.eq(1).all())
        self.assertTrue(tables['daily'].full_day_wh.eq(0).all())

    def test_weekday_hour_sample_counts(self):
        rows = compare(self.db,'2026-04-01','2026-04-01')['weekday_hour']
        item = rows.query('room_id==3 and weekday==2 and hour==8').iloc[0]
        self.assertEqual(item.expected_hours,1)
        self.assertEqual(item.measured_hours,0)
        self.assertTrue(pd.isna(item.mean_wh))
        self.assertEqual(rows.query('weekday!=2').expected_hours.sum(),0)

    def test_invalid_ranges(self):
        for first,last in [('2026-03-31','2026-04-01'),('2026-04-02','2026-04-01'),
                           ('2026-04-31','2026-04-31')]:
            with self.subTest(first=first,last=last),self.assertRaises(ValueError):
                period(first,last)

    def test_duplicate_reading_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError),connect(self.db,False) as connection:
            connection.execute("INSERT INTO readings VALUES(1,'2026-04-01 00:00:00',1)")

    def test_invalid_readings_rejected(self):
        rows = [(1,'2026-04-02 00:00:00',-1),(1,'2026-04-02 00:00:00',1.5),
                (2,'2026-04-02 00:15:00',50),(2,'2026-04-02 00:00:00Z',50),
                (2,'2026-05-01 00:00:00',50),(99,'2026-04-02 00:00:00',50),
                (2,'2026-04-02 00:00:00',None)]
        for row in rows:
            # Room 2 has no readings on April 2, so value checks exercise a free key.
            if row[0] == 1:
                row = (2,row[1],row[2])
            with self.subTest(row=row),self.assertRaises(sqlite3.IntegrityError):
                with connect(self.db,False) as connection:
                    connection.execute('INSERT INTO readings VALUES(?,?,?)',row)

    def test_read_only_connection(self):
        with self.assertRaises(sqlite3.OperationalError),connect(self.db) as connection:
            connection.execute('DELETE FROM readings')

    def test_seed_repeatability(self):
        self.assertEqual(generate(),generate(42))
        self.assertNotEqual(generate(),generate(43))

    def test_prepare_preserves_database(self):
        before = self.db.read_bytes()
        prepare(self.db,self.root/'source')
        self.assertEqual(self.db.read_bytes(),before)
        self.assertEqual(len(list((self.root/'source').glob('*.csv'))),3)

    def test_atomic_creation_failure(self):
        data = generate()
        data['readings'].append(data['readings'][0])
        target = self.root/'broken.db'
        with self.assertRaises(sqlite3.IntegrityError):
            create(target,data)
        self.assertEqual(list(self.root.glob('*.db')),[self.db])

    def test_export_no_readings(self):
        with connect(self.db,False) as connection:
            connection.execute('DELETE FROM readings')
        output = self.root/'results'
        tables = export(self.db,'2026-04-02','2026-04-02',output)
        self.assertEqual(len(tables['hourly']),72)
        self.assertTrue(tables['daily'].recorded_wh.isna().all())
        self.assertEqual(len(list(output.glob('*.png'))),4)
        self.assertEqual(len(list(output.glob('*.csv'))),6)
        self.assertTrue((output/'report.md').exists())

    def test_export_stops_on_mismatch(self):
        output = self.root/'results'
        with patch('electricity_lab.analyze.compare',side_effect=ValueError('simulated mismatch')):
            with self.assertRaises(ValueError):
                export(self.db,out=output)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
