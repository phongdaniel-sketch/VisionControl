# Retest sau thay đổi setting camera — 05/09/2026

Không thay setting trong lần đo. 720p/60, DirectShow, MJPG xác nhận, hai lượt
camera-only / sequential / latest. Thời lượng đo khoảng 6 giây sau warmup 1 giây.
Exposure driver trả -5, gain 0; auto-exposure trả -1 (không diễn giải giá trị
không được hỗ trợ này thành trạng thái bật/tắt). Ảnh người dùng cho thấy Auto
White Balance vẫn bật, HDR/Auto Focus/Auto Exposure tắt; low-light compensation
không xuất hiện trong phần ảnh mới nên không xác nhận riêng được trạng thái đó.

| Chế độ | Lượt 1 | Lượt 2 | Tải nhận diện |
| --- | --- | --- | --- |
| Chỉ camera | 33,42 FPS | 33,17 FPS | Không chạy model |
| Tuần tự | 28,49 FPS | 33,51 FPS | Lượt 1 xen kẽ 0/1/2 tay; lượt 2 toàn bộ không có tay |
| Latest-frame | 24,83 FPS | 28,40 FPS | Lượt 1 toàn bộ 1 tay; lượt 2 có/không có tay |

So với trước ~19,9 FPS camera-only, tốc độ đọc hiện tăng rõ lên ~33,3 FPS.
Không dùng 33,51 FPS lúc không tay để tuyên bố tốc độ tracking tay. Khi có tải
tracking, các lượt đạt khoảng 25–28,5 FPS, không phải 60. Không có UI hoặc OS
input trong benchmark; chưa đo FPS Controller đầy đủ. Không đủ bằng chứng
latest-frame tăng throughput; tuổi kết quả p95 ở latest là 63–78 ms sau read.
Số sequence bị bỏ 50 và 29 chứng minh consumer bỏ frame khi bận; không xử lý lại
cùng ID. Chưa xác minh từng read là exposure độc lập.

USB query vẫn Speed=2, V2 Flags=2: USB2 High-Speed, SuperSpeed capable nhưng không
operating. Cùng đường USB mà tốc độ đọc tăng sau thay setting: chưa thể quy lỗi
hoàn toàn cho USB/DirectShow/OpenCV. Phơi sáng -5 nếu theo chuẩn log2 giây của
Windows tương ứng 31,25 ms; đó là hạn chế tiềm năng với mục tiêu 60 exposure/s,
không phải đo trực tiếp shutter thực. Chưa đổi sang -6 hoặc thay mức sáng.

Latest landmark + One Euro Filter + velocity prediction phù hợp làm thử nghiệm
độ mượt tách biệt: lọc trên sample mới theo timestamp, ước lượng vận tốc từ mẫu
thật đã lọc, dự đoán thời gian ngắn có giới hạn và triệt tốc độ khi mẫu cũ.
Không đưa điểm dự đoán ngược vào bộ lọc như sample đo, không tạo pinch/click từ
dự đoán; pause, mất tay, calibration và click anchor hủy dự đoán. Đổi hướng và
đứng yên cần test overshoot. Cập nhật cursor 60Hz không tạo ra inference 60FPS.
Chưa triển khai thay đổi controller trong lượt retest.

Artifacts: build/effects-off-benchmark.json, build/brio-usb-link.json.
Nguồn: https://gery.casiez.net/1euro/
https://learn.microsoft.com/en-us/uwp/api/windows.media.devices.videodevicecontroller.exposure
