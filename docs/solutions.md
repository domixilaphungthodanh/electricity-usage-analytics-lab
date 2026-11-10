# Lời giải

Chạy các biểu thức trong ô Python của notebook.

## 1. Liệt kê phòng

~~~python
read_sql('SELECT * FROM rooms ORDER BY room_id')
~~~

## 2. Đếm số đo nguồn

~~~python
read_sql('SELECT COUNT(*) AS n FROM readings')
~~~

## 3. Xem giờ đầu và cuối

~~~python
read_sql('SELECT MIN(hour_start),MAX(hour_start) FROM readings')
~~~

## 4. Lọc phòng ngủ

~~~python
read_sql('SELECT * FROM readings WHERE room_id=2 LIMIT 10')
~~~

## 5. Đếm số đo 0 Wh

~~~python
read_sql('SELECT COUNT(*) FROM readings WHERE wh=0')
~~~

## 6. Quy đổi Wh sang kWh

~~~python
read_sql('SELECT hour_start,wh/1000.0 AS kwh FROM readings LIMIT 10')
~~~

## 7. Kiểm tra một ngày có 72 ô

~~~python
sql_tables(db,'2026-04-01','2026-04-01')['hourly'].shape[0]
~~~

## 8. Tìm giờ thiếu

~~~python
sql_tables(db)['hourly'].query('wh.isna()')
~~~

## 9. Tìm ngày thiếu toàn bộ

~~~python
sql_tables(db)['daily'].query('measured_hours==0')
~~~

## 10. Tính độ bao phủ phòng làm việc 01/04

~~~python
sql_tables(db,'2026-04-01','2026-04-01')['daily'].query('room_id==3').coverage_pct
~~~

## 11. Tìm ngày đủ số đo

~~~python
sql_tables(db)['daily'].query('measured_hours==24')
~~~

## 12. Tìm ngày cao nhất trong từng phòng

~~~python
sql_tables(db)['daily'].query('day_rank==1')
~~~

## 13. Đọc số ngày chung

~~~python
sql_tables(db)['room_comparison'][['room','common_days']]
~~~

## 14. So phòng trong ba ngày đầu

~~~python
sql_tables(db,'2026-04-01','2026-04-03')['room_comparison']
~~~

## 15. Tìm thứ–giờ thiếu mọi mẫu

~~~python
sql_tables(db)['weekday_hour'].query('expected_hours>0 and measured_hours==0')
~~~

## 16. Xem trung bình lúc 20:00

~~~python
sql_tables(db)['weekday_hour'].query('hour==20')
~~~

## 17. Tìm giờ cao điểm toàn nhà

~~~python
sql_tables(db)['whole_house_hours'].query('peak_rank==1')
~~~

## 18. Đếm giờ đủ ba số đo

~~~python
len(sql_tables(db)['whole_house_hours'])
~~~

## 19. Kiểm tra tổng dự kiến, đo và thiếu

~~~python
compare(db)['quality']
~~~

## 20. Đối chiếu SQL và pandas trong một tuần

~~~python
compare(db,'2026-04-01','2026-04-07')
~~~