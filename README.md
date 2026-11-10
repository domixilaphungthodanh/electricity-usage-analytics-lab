# Electricity Usage Analytics Lab

Học SQL qua **điện năng giả lập theo giờ** của ba phòng trong tháng 4/2026. Dùng Python 3.12, SQLite, pandas, Seaborn, Matplotlib và Jupyter. Menu chỉ tra cứu. Mã MIT.

## Bắt đầu trên Windows PowerShell

Giải nén toàn bộ ZIP, mở thư mục chứa run_electricity.py trong File Explorer, gõ PowerShell trên thanh địa chỉ rồi Enter. Dùng Python 3.12 và mạng khi cài thư viện lần đầu. [Bản phát hành](https://github.com/domixilaphungthodanh/electricity-usage-analytics-lab/releases)

~~~powershell
Get-Location
Get-ChildItem
python src/prepare_data.py
python src/analyze.py
python run_electricity.py --notebook
~~~

Nếu chưa thấy run_electricity.py, dùng cd "đường dẫn thư mục dự án". Mở notebooks/02_analysis.ipynb và nhấn **Shift+Enter** từng ô từ trên xuống. Nếu thấy tab Running, chuyển sang Files rồi mở notebook. Giữ PowerShell mở trong lúc học.

Dùng python run_electricity.py cho menu. START_WINDOWS.cmd mở menu và START_NOTEBOOK.cmd mở notebook. Launcher dùng môi trường đường dẫn ngắn trên Windows và gọi python -m notebook.

## Kỳ và database

~~~powershell
python src/prepare_data.py --db database/practice.db
python src/analyze.py --db database/practice.db --start 2026-04-01 --end 2026-04-07 --out outputs/week1
python run_electricity.py --notebook --db database/practice.db
~~~

Mặc định dùng database/electricity.db và toàn tháng 4. Hai đầu khoảng ngày đều được tính theo giờ Việt Nam. Prepare chỉ tạo khi thiếu DB, chạy lại kiểm tra và xuất CSV nguồn vào data/raw. Database mới được kiểm tra cấu trúc, khóa ngoại và phòng trước khi công bố.

## Đọc kết quả

- Seed 42 tạo **2.160 ô dự kiến**, **2.084 số đo**, **76 ô thiếu**, trong đó có **78 số đo bằng 0 Wh**.
- Một số đo là điện năng của một giờ. Chia 1.000 để đổi Wh sang kWh. Số đo 0 Wh vẫn được tính vào độ bao phủ.
- Phòng làm việc ngày 01/04 có 20/24 giờ, độ bao phủ 83,3%. CSV giữ tổng đã ghi nhận, tổng cả ngày để trống.
- So phòng trên cùng tập ngày cả ba phòng đủ 24 số đo. Giờ cao điểm được xét trong tập giờ đủ ba số đo. Các giờ đồng mức cao nhất cùng hạng 1.
- Kết quả trong outputs gồm hourly, daily, room_comparison, weekday_hour, whole_house_hours, quality, bốn PNG và report.md. Quality kiểm tra toàn DB, năm bảng kia theo kỳ chọn.

## Học SQL

Bắt đầu với ví dụ 20/24 giờ trong notebook tổng hợp, rồi làm tám bài chuyên sâu. Các notebook truy vấn bằng kết nối SQLite chỉ đọc. [Notebook tổng hợp](notebooks/02_analysis.ipynb) · [Từ điển dữ liệu](docs/data_dictionary.md) · [Bảng tra lệnh](docs/commands.md)

Tự làm trước khi mở lời giải. [20 bài tập](docs/exercises.md) · [Lời giải](docs/solutions.md)

~~~powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m electricity_lab.execute_notebooks
~~~

Actions kiểm thử Windows/Linux khi push hoặc PR. Workflow thủ công tạo mẫu, phân tích và chạy chín notebook, giữ artifact 14 ngày. ZIP chứa mã, tài liệu và notebook nguồn.
