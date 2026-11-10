import argparse

from .analysis import sql_tables
from .analyze import export
from .db import DEFAULT_DB
from .prepare_data import validate
from .sample import START, END, ROOMS


def pages(frame):
    if frame.empty:
        print('Kỳ này chưa có kết quả.')
    for offset in range(0,len(frame),20):
        print(frame.iloc[offset:offset+20].to_string(index=False))
        if offset+20 < len(frame) and input('Enter xem tiếp, q quay lại ').strip().lower() == 'q':
            return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db',default=str(DEFAULT_DB))
    args = parser.parse_args()
    quality = validate(args.db)
    while True:
        print('\nĐIỆN NĂNG GIẢ LẬP\n1. Chất lượng dữ liệu\n2. Số đo theo giờ\n3. Ngày thiếu số đo\n4. So phòng theo ngày chung\n5. Giờ cao điểm\n6. Xuất báo cáo\n0. Thoát')
        try:
            option = input('Chọn số ').strip()
            if option == '0':
                return
            if option == '1':
                pages(quality)
                continue
            if option not in ('2','3','4','5','6'):
                print('Nhập một số từ 0 đến 6.')
                continue
            start = input(f'Từ ngày [{START}] ').strip() or START
            if start.lower() == 'q':
                continue
            end = input(f'Đến ngày [{END}] ').strip() or END
            if end.lower() == 'q':
                continue
            if option == '6':
                export(args.db,start,end)
                continue
            tables = sql_tables(args.db,start,end)
            if option in ('2','3'):
                for number, name in ROOMS:
                    print(f'{number}. {name}')
                selection = input('Chọn phòng hoặc Enter xem tất cả ').strip()
                if selection.lower() == 'q':
                    continue
                if selection and selection not in ('1','2','3'):
                    print('Chọn số phòng 1–3.')
                    continue
                frame = tables['hourly'] if option == '2' else tables['daily'].query('missing_hours > 0')
                if selection:
                    frame = frame[frame.room_id == int(selection)]
                pages(frame)
            elif option == '4':
                pages(tables['room_comparison'])
            else:
                pages(tables['whole_house_hours'].query('peak_rank == 1'))
        except ValueError as exc:
            print(exc)
        except (EOFError,KeyboardInterrupt):
            return


if __name__ == '__main__':
    main()
