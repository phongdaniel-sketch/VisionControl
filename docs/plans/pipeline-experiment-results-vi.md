# Kết quả chạy thử pipeline — 05/09/2026

Đã chạy camera 0, DirectShow, MJPG được driver xác nhận, kích thước thực đúng.
Mỗi lượt bỏ 1 giây đầu và đo khoảng 6 giây; hai lượt mỗi chế độ. Lượt đầu
latest-frame 480p hết thời gian mở camera (5 giây); đã tăng thời gian khởi động
lên 20 giây, giữ chờ ảnh tiếp theo 5 giây và chạy bù thành công. Mỗi case chạy
trong process độc lập với timeout 35 giây.

| Chế độ | Chỉ đọc camera | Tuần tự + nhận diện | Luồng ảnh mới nhất + nhận diện |
| --- | --- | --- | --- |
| 640x480/30 | 17,38 / 17,01 FPS | 17,30 / 19,99 FPS | 18,93 / 20,60 FPS (gồm lượt bù) |
| 1280x720/60 | 19,99 / 19,87 FPS | 19,83 / 19,98 FPS | 19,99 / 19,99 FPS |

## Diễn giải

- 720p: đa luồng chưa cho thấy cải thiện đáng kể. Camera-only cũng khoảng 20 FPS,
  dù driver báo 60 FPS. Giới hạn nằm ít nhất một phần ở đường lấy ảnh/thiết bị/
  điều kiện hiện tại; chưa xác định được exposure, USB hay backend là nguyên nhân.
- Nhận diện trung vị khoảng 31–32 ms. Đổi sang đọc luồng riêng không làm mô hình
  nhanh hơn. Không có sequence ID bị bỏ trong các lượt thành công, phù hợp với
  tốc độ đọc ảnh thấp hơn khả năng xử lý ở tải này.
- 480p dao động giữa các lượt. Không đủ bằng chứng quy mức tăng nhỏ cho threading.
- Số tay hiện diện thay đổi (phần lớn một tay, một số lượt hai tay); không phải
  phép thử độ chính xác hay cùng chuỗi thao tác. FPS là số read/kết quả, không
  chứng minh mỗi ảnh là một exposure mới. Tuổi kết quả tính từ sau read, không
  đo cảm biến/driver. Không có Qt, điều khiển chuột hoặc ghi video trong benchmark.
- 720p tốt hơn lượt cũ 10 FPS nhưng không đủ cô lập nguyên nhân: script lần này
  đặt FOURCC cuối cùng và điều kiện camera/tay có thể khác. Không khẳng định
  thứ tự set đã sửa nguyên nhân. Chưa đổi mặc định app.

## Tiếp theo

Đo camera-only dưới điều kiện ánh sáng/exposure kiểm soát, kiểm tra kết nối USB
và so sánh backend trong process có timeout. Sau khi camera cung cấp ảnh nhanh
hơn, đo lại pipeline và mới quyết định tích hợp luồng riêng. Việc tách inference
khỏi UI vẫn hữu ích cho Pause/giao diện, nhưng chưa được đo trong thử nghiệm này.

## Artifacts

- Script: `scripts/benchmark_pipeline.py`.
- Số đo gốc: `build/pipeline-experiment.json` (giữ cả lỗi khởi động để truy vết).
- Lượt chạy bù: `build/pipeline-latest-480-retry.json`.
- 99 deterministic tests passed; compileall và diff check passed trước chỉnh
  thời gian chờ; compileall/diff được chạy lại sau chỉnh sửa cuối.
- Camera đã được nhả khi kết thúc. Không lưu ảnh, không đổi calibration/profile,
  không tích hợp benchmark vào runtime sản phẩm.
