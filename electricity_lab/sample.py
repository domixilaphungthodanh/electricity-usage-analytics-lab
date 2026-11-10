from random import Random

START = '2026-04-01'
END = '2026-04-30'
ROOMS = [(1, 'Phòng khách'), (2, 'Phòng ngủ'), (3, 'Phòng làm việc')]
EXPECTED = 30 * 24 * len(ROOMS)
TABLES = ['rooms', 'readings', 'metadata']


def generate(seed=42):
    rng = Random(seed)
    readings = []
    for room_id, _ in ROOMS:
        for day in range(1, 31):
            for hour in range(24):
                active = (
                    (room_id == 1 and 18 <= hour <= 22)
                    or (room_id == 2 and (hour >= 22 or hour <= 6))
                    or (room_id == 3 and 8 <= hour <= 17)
                )
                wh = rng.randint(180, 560) if active else rng.randint(0, 120)
                draw = rng.random()
                if (day == 1 and room_id == 3 and 8 <= hour <= 11) or (day == 2 and room_id == 2):
                    continue
                if day > 3 and draw < 0.035:
                    continue
                if draw > 0.97 or (room_id, day, hour) == (1, 1, 0):
                    wh = 0
                readings.append((room_id, f'2026-04-{day:02d} {hour:02d}:00:00', wh))
    metadata = [('data_kind', 'simulated'), ('seed', str(seed)), ('version', '1.0.0'),
                ('period', '2026-04'), ('timezone', 'Asia/Ho_Chi_Minh'), ('unit', 'Wh per hour')]
    return dict(rooms=ROOMS, readings=readings, metadata=metadata)
