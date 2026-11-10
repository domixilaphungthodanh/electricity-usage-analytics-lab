# Từ điển dữ liệu

| Bảng | Cấp dữ liệu và khóa |
|---|---|
| rooms | Một phòng, khóa room_id |
| readings | Một phòng và giờ bắt đầu, khóa ghép room_id và hour_start |
| metadata | Nhãn giả lập, seed, phiên bản, kỳ, múi giờ và đơn vị |

~~~mermaid
erDiagram
    rooms ||--o{ readings : measured
~~~

hour_start theo giờ Việt Nam và có dạng YYYY-MM-DD HH:00:00. wh là số nguyên từ 0 đến 1 tỷ, giới hạn kỹ thuật giúp giữ tổng Wh chính xác trong cửa sổ mẫu. Lịch đầy đủ được tạo từ khoảng ngày và kết hợp với danh sách phòng. LEFT JOIN đưa vào NULL ở các ô thiếu bản ghi. COUNT(wh) đếm cả 0 Wh. COUNT(*) trên lịch là số giờ dự kiến.

| CSV | Cấp dữ liệu và chỉ số |
|---|---|
| hourly | Phòng và giờ, ngày, thứ, giờ đồng hồ, Wh có thể trống |
| daily | Phòng và ngày, số giờ dự kiến, đo được, thiếu, độ bao phủ, recorded_wh, full_day_wh, common_day, day_rank |
| room_comparison | Một phòng, số ngày chung và tổng Wh của đúng các ngày đó |
| weekday_hour | Phòng, thứ và giờ đồng hồ, số giờ dự kiến, số mẫu và Wh trung bình |
| whole_house_hours | Giờ đủ cả ba số đo, tổng Wh và hạng cao điểm |
| quality | Số ô dự kiến, số đo, ô thiếu và số đo bằng 0 của toàn DB |

weekday lấy thứ Hai = 0, Chủ nhật = 6. Ô thứ–giờ ngoài kỳ chọn có 0 giờ dự kiến và trung bình trống. Ô có giờ dự kiến nhưng thiếu mọi số đo cũng giữ trung bình trống. Tổng lượng ghi nhận dùng SUM hoặc sum(min_count=1). Chỉ các ngày đủ 24 giờ có full_day_wh và được xếp hạng giảm dần trong từng phòng. Đồng tổng cùng hạng. So phòng dùng các ngày common_day=1. Nếu không có ngày chung, tổng trống và số ngày bằng 0. Tất cả giờ đồng mức đỉnh có peak_rank=1.

Đếm và tổng Wh được đối chiếu chính xác giữa SQL và pandas. Tỷ lệ và trung bình dùng sai số tuyệt đối tối đa 1e-8.
