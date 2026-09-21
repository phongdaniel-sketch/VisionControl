# Chạy thử Gesture Hand v1

Bản thử nghiệm đã có code cho các nhóm thao tác trong yêu cầu v1.0; chưa nghiệm
thu độ chính xác trên các video thao tác mới của người dùng. Không coi test
trạng thái giả lập hoặc việc mở camera thành công là nhận diện đúng mọi tư thế.

## Mở app

```powershell
$env:PYTHONPATH='src'
$env:VISION_CONTROL_CAMERA_PRESET='720p30'
.\.venv311\Scripts\python.exe -m vision_control.launcher --camera-index 0 --start-paused
```

Mở Settings → Gesture v1. Profile hiện tại đã bật v1 và hai tay. Mapping 1–5
ngón, symbol và hotcorner mới đều trống. Nắm tay phải 3 giây để switch hai tay
mặc định Off; bật tùy chọn riêng nếu muốn. Nắm tay trái không còn ARMED.

Các công tắc cuộn, zoom, âm lượng có thể tắt độc lập khi cần cô lập lỗi nhận diện.
Nhấn Save sẽ khởi động lại camera ở Pause. V1 sử dụng Thumb lock cho chuột.
Mapping cũ ở trang Gestures không điều khiển tay trái khi v1 bật.

## Thao tác

| Tay | Tư thế / chuỗi | Kết quả |
| --- | --- | --- |
| Chuột | Cái khép / mở | Di chuyển theo trỏ / khóa |
| Chuột | Cái mở: co rồi duỗi ngón trỏ / cả trỏ và giữa | Click trái / giữa |
| Chuột | Tách cái khỏi trỏ/giữa, rồi chạm cái với giữa | Click phải ngay lúc chạm; giữ không lặp |
| Chuột | Tách cái–trỏ trước, pinch 100 ms | Bắt đầu drag; di chuyển lòng bàn tay |
| Chuột | Tách pinch 100 ms | Thả drag |
| Chuột | Cái mở, bốn ngón duỗi khép sát; dịch chuyển | Cuộn dọc/ngang; trục giữ đến khi rời tư thế |
| Chuột | Xòe rộng → chụm / chụm → xòe | Zoom in / out |
| Chuột | Các đầu ngón hướng camera hơi chụm, xoay | Thuận chiều kim đồng hồ trong preview: tăng volume; ngược: giảm |
| Chuột | Thumbs up/down, OK, Victory | Hành động đã gán, phát một lần mỗi lần giữ tư thế |
| Chuột | Vào góc đã gán, nắm–thả hai lần | Hành động của góc |
| Chuột | Fist 3 giây, nếu tùy chọn bật | Toggle input tay phụ, có tiến độ; giữ tiếp không lặp |
| Phụ | Fist ổn định 1 giây | Giữ Ctrl |
| Phụ | Năm ngón duỗi khép sát, cái cũng duỗi, 1 giây | Giữ Shift |
| Phụ | Cái–trỏ chạm nhau 1 giây | Giữ Alt |
| Phụ | 1–5 ngón theo guide | Mapping tự gán; 5 ngón phải xòe rộng |

Rời tư thế modifier là nhả phím. Pause, mất tay, dữ liệu trễ, tắt hai tay, lỗi
và thoát vẫn nhả input. Fist phải vẫn nhả nút chuột trước các hành động khác.

## Gán hành động

Nhập tổ hợp phím như `ctrl+c`, `win+d`, `win+tab` hoặc các tên có sẵn:
`volume_up`, `volume_down`, `mute`, `zoom_in`, `zoom_out`. Để trống để không gán.
Đây chưa phải danh sách đầy đủ mọi hành động Hot Corners của macOS.

OK dùng cái–trỏ chạm, ba ngón còn lại duỗi. Nếu đã gán OK, tư thế này được
ưu tiên làm symbol thay vì bắt đầu drag. Đang drag không chuyển thành OK.
Nếu khó drag, để OK trống trong lúc kiểm chứng hoặc co nhẹ ba ngón còn lại.
Không thể phân biệt hai ý định có tư thế và chuỗi chuyển động giống hệt nhau.

Zoom dùng shortcut Ctrl+=/Ctrl+- trên Windows, Cmd+=/Cmd+- trên macOS;
ứng dụng đích phải hỗ trợ. Chưa xác nhận mọi ứng dụng hoặc macOS bằng máy thật.
Cuộn/zoom/volume được ưu tiên theo tư thế khởi đầu. Ngưỡng khép/xòe và tư thế
đầu ngón hướng camera là heuristic cần video để cân chỉnh, không phải model
đã được huấn luyện riêng cho bàn tay người dùng.

## Thử và ghi debug

1. Thử move/lock/click/drag trước, tạm tắt các chức năng khác nếu bị tranh tư thế.
2. Thử từng modifier: chờ đủ 1 giây; thả và kiểm tra phím đã nhả.
3. Thử cuộn dọc và ngang trên nội dung thực sự có hai trục cuộn.
4. Gán từng symbol/hotcorner rồi thử; tránh gán nhiều chức năng khi chưa kiểm chứng.
5. Thử zoom/volume từng nhóm. Bật Debug → Debug recording để ghi mẫu cục bộ;
   cửa sổ này dùng input giả lập, không thay đổi volume hoặc ứng dụng thật.

Video mỗi nhóm nên có nghỉ → tư thế đầu → động tác → thả, vài lần mỗi chiều,
đồng thời có động tác gần giống nhưng không muốn kích hoạt. Nhãn trạng thái
trong debug giúp đối chiếu ý định. Đừng dùng FPS recorder để suy ra FPS Controller
vì hai đường xử lý vẫn khác nhau. Không tự tải video lên hay tự huấn luyện model.

Replay cục bộ không điều khiển PC:

```powershell
.\.venv311\Scripts\python.exe scripts/replay_gesture_v1.py PATH_TO_frames.jsonl config/gesture_v1_profile.json
```

## Cấu hình và hoàn tác

Profile mới: `config/gesture_v1_profile.json`. Profile cá nhân đã giữ nguyên
calibration và mapping cũ; bản sao trước chuyển đổi nằm ở
`data/user_profile.json.pre-gesture-v1.bak`. Tắt Enable Gesture Hand v1 rồi Save
để dùng lại cơ chế cũ. Không cần build exe cho vòng thử này.

## Cập nhật: hai mode con trỏ, một trang Gestures

- Mouse → Palm (mặc định): theo tâm lòng bàn tay; mở ngón cái không khóa.
  Vẫn mở cái để thực hiện click bằng co–duỗi ngón.
- Mouse → Index fingertip: theo đầu ngón trỏ; mở cái khóa như trước.
- Gestures là trang cấu hình duy nhất, thay cho menu Gesture v1. Không còn công
  tắc bật/tắt bộ cử chỉ. Những hướng dẫn về menu/toggle cũ phía trên là lịch sử.
- Cuộn ở palm dùng cái mở + bốn ngón duỗi khép sát; tạm giữ con trỏ. Bàn tay
  xòe thông thường vẫn di chuyển; chỉ chuỗi zoom thực sự mới giữ con trỏ.
- Drag 100 ms và quy tắc OK giữ nguyên ở cả hai mode: OK có ba ngón còn lại duỗi
  và chỉ chiếm pinch nếu được gán hành động; đang drag không đổi thành OK.
- Calibrate riêng từng mode. Palm dùng dấu tím ở tâm bàn tay và lưu
  mouse_calibration_palm.json; dấu I8/T4 vẫn hiện và calibration đầu ngón cũ
  không bị ghi đè. Mode palm lần đầu cần Calibrate, không cần gán lại cử chỉ.
