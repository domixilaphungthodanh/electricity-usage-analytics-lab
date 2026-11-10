# Bảng tra lệnh

| Lệnh | Nơi nhập và công dụng |
|---|---|
| Get-Location | PowerShell, xem thư mục hiện tại |
| Get-ChildItem | PowerShell, tìm run_electricity.py và src |
| cd "đường dẫn" | PowerShell, chuyển thư mục |
| python src/prepare_data.py | PowerShell, tạo mẫu và xuất CSV nguồn |
| python src/analyze.py | PowerShell, đối chiếu và xuất báo cáo |
| python run_electricity.py --notebook | PowerShell, mở notebook |
| 0–6 | Menu tra cứu |
| read_sql("SELECT ...") | Ô Python trong notebook |

WITH RECURSIVE tạo lịch. CROSS JOIN ghép giờ với phòng. LEFT JOIN giữ ô lịch khi thiếu số đo. COUNT(wh) bỏ NULL, còn SUM(wh) giữ NULL nếu cả nhóm thiếu. HAVING lọc nhóm đủ số đo. DENSE_RANK giữ các trường hợp đồng hạng.
