# Phương án tối ưu hiệu năng VisionControl

Ngày khảo sát: 05/09/2026. Đây là kết quả nghiên cứu và kế hoạch, chưa phải thay đổi runtime.

## Kết luận

Ưu tiên đo riêng đường lấy ảnh Brio, sau đó tách đọc camera / nhận diện / giao diện.
Chỉ giữ khung hình mới nhất, không xếp hàng ảnh cũ. Chưa chọn 720p/60 làm mặc định
và chưa cam kết đạt 60 kết quả nhận diện mỗi giây.

## Bằng chứng trong workspace

`build/brio-mode-measurement.json`: mỗi chế độ đo 60 khung sau 10 khung làm nóng;
không phải chuỗi động tác giống nhau, không phải thử nghiệm độ chính xác.

| Yêu cầu | Đọc ảnh trung vị | Nhận diện trung vị | Đọc + nhận diện |
| --- | --- | --- | --- |
| 640x480/30 | 15,33 ms | 34,50 ms | 19,82 FPS |
| 1280x720/60 | 60,01 ms | 36,49 ms | 10,01 FPS |
| 1920x1080/60 | 153,41 ms | 42,99 ms | 5,00 FPS |

Script đã yêu cầu MJPG nhưng chưa xác nhận FOURCC thực sự được driver thương lượng.
Chưa đo camera riêng, USB link speed, exposure, ảnh lặp hay tuổi ảnh trong driver.
Không thể quy toàn bộ chậm ở HD cho MediaPipe hoặc kết luận camera thực chỉ 10 FPS.

`Camera.read()` và `detect_for_video()` hiện chạy tuần tự trên vòng xử lý giao diện.
Tracker dùng CPU, VIDEO, tối đa hai tay. VIDEO đã tái sử dụng tracking; đổi sang
LIVE_STREAM không tự làm mô hình suy luận nhanh hơn. UI chuyển ảnh, scale và cập
nhật nhiều widget mỗi kết quả. Ghi AVI/JSONL debug hiện đồng bộ.

## Thứ tự triển khai đề xuất

### 1. Đo và chọn chế độ camera thực

- Benchmark chỉ đọc camera, không MediaPipe/Qt/ghi video; sau đó thêm từng tầng.
- Ghi backend, kích thước thực, FPS driver báo, FOURCC thực, thời gian read p50/p95,
  số khung mới và timestamp. FPS driver báo không thay thế tốc độ đo.
- So sánh DirectShow với MSMF trong tiến trình thử riêng có timeout; MSMF từng
  có rủi ro treo khi mở, không đổi backend mặc định mù quáng.
- Đối chiếu MJPG và các mode được thiết bị công bố; kiểm tra kết nối USB và
  ánh sáng/exposure nếu camera-only vẫn chậm. Không đổi exposure bền vững tự động.
- Cùng ánh sáng, cùng số tay, cùng động tác, lặp lại mỗi cấu hình để so sánh công bằng.

### 2. Đọc camera riêng, chỉ giữ ảnh mới nhất

Một worker sở hữu toàn bộ vòng đời VideoCapture, lưu một frame mới nhất kèm
sequence ID và timestamp sau read. Consumer chỉ xử lý ID mới một lần; ảnh chưa
xử lý bị thay khi có ảnh mới. Không dùng hàng đợi vô hạn, không đếm nhiều lần cùng
frame thành FPS. Threading giảm chờ I/O; không bảo đảm tăng tốc inference CPU.

Giữ quyền sở hữu ảnh rõ ràng: UI không vẽ lên buffer inference đang sử dụng.
Dừng worker trước khi mở camera trong Settings/debug; không release/read đồng thời.

### 3. Nhận diện ngoài UI, kết quả mới nhất

Ưu tiên một worker dùng VIDEO để giảm phạm vi thay đổi; hoặc thử LIVE_STREAM với
`detect_async` và callback có timestamp. Chỉ chọn một cơ chế điều phối inference,
không chạy nhiều tracker cạnh tranh để làm đẹp FPS.

Callback không trực tiếp gửi input hoặc sửa QWidget. Chủ sở hữu controller nhận
kết quả qua tín hiệu/hộp kết quả mới nhất; loại kết quả cũ theo session generation
và tuổi kết quả. Pause phải nhả nút ngay cả khi inference đang chậm. Watchdog khi
không có kết quả mới phải nhả input; không tiếp tục kéo bằng landmark cũ.

### 4. Giảm việc không cần chạy ở tốc độ camera

- Preview khoảng 30 FPS, text status 5–10 lần/giây, nhận diện chạy độc lập.
- Đo chi phí copy/scale trước khi thay cách render.
- Ghi debug bằng worker có hàng đợi giới hạn; frame ID phải khớp video/log và ghi
  rõ dropped frames. Khi worker lỗi phải dừng ghi và báo lỗi, không tích RAM.
- Thử 720p camera với ảnh inference resize giữ nguyên tỷ lệ. Nếu crop ROI, bắt
  buộc chuyển tọa độ ngược về ảnh gốc, xử lý mất tay và hai tay trước khi dùng.
- Chỉ thử num_hands=1 trong chế độ người dùng chủ động tắt điều khiển bàn phím;
  không hy sinh chức năng hai tay mặc định để tăng FPS.

### 5. Tiêu chí nghiệm thu

Báo riêng capture FPS, inference FPS, preview FPS; p50/p95 thời gian và tuổi kết
quả sau read (không gọi là độ trễ cảm biến). Đánh giá vị trí khi giữ yên, tỷ lệ
click đúng, nhầm nút, pause/mất tay/đóng app/đổi camera. Không đặt thành công bằng
con số FPS đơn lẻ. Mục tiêu ban đầu: giảm tuổi kết quả và chờ UI, sau đó kiểm chứng
khả năng khoảng 30 inference FPS; đây là mục tiêu, chưa phải kết quả đo.

## Nguồn đối chiếu

- [GitHub imutils WebcamVideoStream](https://github.com/PyImageSearch/imutils/blob/master/imutils/video/webcamvideostream.py): ví dụ đọc camera trong thread riêng. Cần bổ sung sequence ID, ownership và shutdown cho app; không sao chép nguyên xi.
- [MediaPipe Hand Landmarker Python](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python): VIDEO đồng bộ, LIVE_STREAM callback; input khi đang bận có thể bị bỏ qua. Đã kiểm tra API detect_async và flow limiting có trong gói 0.10.21 cài tại workspace.
- [OpenCV VideoCapture](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html): thuộc tính phụ thuộc backend/driver/device; phải xác nhận bằng đo thực.
- [OpenCV issue Brio/DirectShow/MJPG #9084](https://github.com/opencv/opencv/issues/9084): báo cáo lịch sử cho thấy codec và thương lượng mode cần kiểm tra. Issue từ 2017, không phải bằng chứng lỗi đó còn tồn tại trong bản 4.11 hiện tại.
- [MediaPipe GPU Windows #5385](https://github.com/google-ai-edge/mediapipe/issues/5385): không xem bật GPU trong Python Windows là sửa đổi một dòng đã được bảo đảm. Cần kiểm chứng hỗ trợ của đúng bản build trước khi chọn hướng GPU.
- [YouTube: Hand Tracking 30 FPS using CPU](https://www.youtube.com/watch?v=NZde8Xt78Iw): tìm thấy qua kết quả tìm kiếm; không truy xuất được video/transcript, chưa xác minh nội dung hoặc benchmark. Không dùng con số trong tiêu đề làm bằng chứng hiệu năng cho máy này.

## Phạm vi lượt nghiên cứu

Đã đọc nguồn, đối chiếu code và số đo có sẵn, lưu kế hoạch này. Chưa thay pipeline,
chưa benchmark camera mới trong lượt này, chưa thay calibration/gesture/profile.
