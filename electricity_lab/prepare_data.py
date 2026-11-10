import argparse
import os
from pathlib import Path
import tempfile

import pandas as pd

from .db import ROOT, DEFAULT_DB, connect
from .sample import EXPECTED, ROOMS, TABLES, generate


def validate(db):
    with connect(db) as connection:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite có lỗi cấu trúc')
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Có liên kết khóa ngoại sai')
        metadata = dict(connection.execute('SELECT * FROM metadata'))
        if metadata.get('data_kind') != 'simulated':
            raise ValueError('Cần database dữ liệu giả lập của dự án')
        if set(connection.execute('SELECT * FROM rooms')) != set(ROOMS):
            raise ValueError('Cần đúng ba phòng của bộ mẫu')
        measured, zeros = connection.execute(
            'SELECT COUNT(*), COUNT(CASE WHEN wh=0 THEN 1 END) FROM readings'
        ).fetchone()
    metrics = {'expected_hours': EXPECTED, 'measured_hours': measured,
               'missing_hours': EXPECTED-measured, 'zero_readings': zeros}
    return pd.DataFrame(metrics.items(), columns=['metric', 'value'])


def create(db=DEFAULT_DB, data=None):
    db = Path(db).resolve()
    if db.exists():
        raise FileExistsError(f'Database đã tồn tại: {db}')
    db.parent.mkdir(parents=True, exist_ok=True)
    data = generate() if data is None else data
    fd, temporary = tempfile.mkstemp(dir=db.parent, suffix='.db')
    os.close(fd)
    try:
        with connect(temporary, False) as connection:
            connection.executescript((ROOT / 'sql/schema.sql').read_text(encoding='utf-8'))
            for table, width in zip(TABLES, [2, 3, 2]):
                placeholders = ','.join('?' for _ in range(width))
                connection.executemany(f'INSERT INTO {table} VALUES({placeholders})', data[table])
        validate(temporary)
        os.link(temporary, db)
    finally:
        Path(temporary).unlink(missing_ok=True)


def prepare(db=DEFAULT_DB, raw_out=None):
    if not Path(db).exists():
        create(db)
    quality = validate(db)
    out = Path(raw_out or ROOT / 'data/raw')
    out.mkdir(parents=True, exist_ok=True)
    with connect(db) as connection:
        for table in TABLES:
            pd.read_sql_query(f'SELECT * FROM {table}', connection).to_csv(
                out / f'{table}.csv', index=False, encoding='utf-8-sig')
    print('Bộ số đo điện năng GIẢ LẬP')
    print(quality.to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(DEFAULT_DB))
    parser.add_argument('--raw-out')
    args = parser.parse_args()
    prepare(args.db, args.raw_out)


if __name__ == '__main__':
    main()
