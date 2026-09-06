# Kế hoạch triển khai Gesture Hand v1.0

Ngày: 06/09/2026. Trạng thái: đã có bản code thử nghiệm cho giai đoạn 1–5;
kiểm thử tự động và camera smoke đã chạy, nghiệm thu bằng tư thế thật còn mở.
Nguồn: [Gesture Hand requirement v1.0](../requirements/Gesture%20Hand%20requirement%20v1.0.md).

## Phạm vi và nguyên tắc

- Windows 11 là môi trường nghiệm thu trước; giữ Python 3.11/MediaPipe 0.10.21
  và kiến trúc adapter để không phá khả năng chạy macOS.
- Đã có move/lock, ba click, pinch drag, filter/prediction, preview toggles.
  Đã bỏ fist arming tay trái. Các phần này phải có kiểm thử hồi quy.
- Không đổi calibration. Drag bắt đầu/thả vẫn mặc định 100 ms; không áp
  thời gian chờ modifier 1 giây sang click/drag.
- Pause, mất tay, dữ liệu quá cũ, calibration, thoát, lỗi: nhả input liên quan;
  tắt chế độ hai tay phải nhả toàn bộ phím tay phụ ngay.
- Không dùng vị trí dự đoán để xác nhận gesture. Không tăng FPS hiển thị bằng
  cách đếm cursor ticks thành inference. Debug mặc định Off, dữ liệu ở máy.
- Mỗi giai đoạn có bản chạy thử riêng; chưa công bố hoàn thành chỉ vì test giả lập qua.

## Giai đoạn 1 — Phân xử cử chỉ, cấu hình và dữ liệu kiểm thử

- Tách đặc trưng hình học (duỗi/co, độ khép/xòe, pinch, hướng lòng bàn tay)
  khỏi quyết định hành động và input adapter. Chuẩn hóa theo kích thước bàn tay,
  xử lý ảnh gương và vai trò tay; không chỉ so sánh tọa độ x/y đầu ngón.
- Thêm trạng thái ứng viên → xác nhận → đang thực hiện → kết thúc/hủy;
  một hành động chính mỗi tay. Tay trái giữ modifier vẫn kết hợp được chuột phải.
- Hành động đang thực hiện sở hữu chuỗi chuyển động: drag không thành OK;
  cuộn không phát click; tư thế chưa rõ không phát hành động mới.
- Kiểm tra bước nhảy landmark và hình học bất thường; đóng băng chuyển động
  khi không đáng tin thay vì dự đoán tiếp từ dữ liệu sai. Ngưỡng cần dữ liệu thật.
- Tạo schema cấu hình có version/migration, toggle từng tính năng và registry
  hành động dùng chung cho symbol/hotcorner. Sao lưu profile cũ; mapping mới
  1–5 ngón mặc định trống, không âm thầm biến W/A/D/S/Space cũ thành mapping mới.
- Bổ sung replay landmark có timestamp; debug ghi ứng viên, lý do từ chối,
  chuyển trạng thái và sự kiện input khi bật. Chuẩn bị mẫu chuyển tiếp và mẫu âm.

Nghiệm thu: cơ chế cũ vẫn chạy, không phát hai hành động xung đột từ cùng một
chuỗi, mọi đường hủy đều nhả input. Migration không mất calibration/profile cũ.

## Giai đoạn 2 — Chế độ hai tay và phím tay trái

- Settings có toggle hai tay; toggle nắm tay phải 3 giây riêng, mặc định Off.
  Khi bật, hiển thị countdown; rời fist hủy, giữ liên tục chỉ toggle một lần,
  phải thả tay để cho phép lần tiếp theo. Chế độ một tay bỏ qua input tay phụ;
  đo hiệu năng trước khi thay số bàn tay tracker vì còn vấn đề chọn đúng vai trò.
- Ctrl: fist. Shift: năm ngón duỗi khép sát. Alt: cái–trỏ chạm nhau.
  Xác nhận ổn định 1 giây, có tiến độ; nhả khi rời tư thế, không chờ 1 giây để nhả.
- Trong ứng viên modifier không phát phím đếm ngón. Năm ngón xòe tách biệt Shift.
- Gán phím/nhấn–giữ cho 1–5 ngón trong Settings, mặc định trống. Dùng chuỗi
  ngón trỏ → giữa → áp út → út → cái cho bộ đếm ban đầu, ghi rõ trong guide;
  không suy ra mọi tổ hợp cùng số ngón đều là một tư thế hợp lệ.
- Không phục hồi ARMED bằng fist. Quản lý quyền giữ phím để các nguồn hành động
  không nhả nhầm modifier của nhau.

Nghiệm thu: không phát modifier trước 1 giây; không giữ kẹt phím sau mất tay,
Pause/tắt hai tay; countdown không lặp toggle; Shift và phím 5 ngón không phát cùng lúc.

## Giai đoạn 3 — Cuộn dọc/ngang

- Tư thế: cái mở, bốn ngón duỗi khép sát; khóa con trỏ tại điểm bắt đầu.
- Xác nhận tư thế rồi dịch chuyển để cuộn. Chọn trục theo hướng chiếm ưu thế,
  có vùng chết và ngưỡng đổi trục riêng để chuyển động chéo không đổi trục liên tục.
- Settings: tốc độ, chiều cuộn, ngưỡng bắt đầu. Hủy/kết thúc cuộn khi rời tư thế;
  bắt lại mốc di chuyển để tránh nhảy cursor sau cuộn.
- Không chỉ dựa vào thumb-open để kích hoạt cuộn, vì đó còn là lock click.

Nghiệm thu: cuộn hai trục trên nội dung có thanh cuộn tương ứng; không click,
không di chuyển cursor trong lúc cuộn; lock-click thường vẫn hoạt động.

## Giai đoạn 4 — Symbol và hot corner

- Nhận Thumbs up/down, OK, Victory; mỗi symbol gán hành động hoặc để trống.
  Giữ tư thế chỉ kích hoạt một lần, có điều kiện thả/reset trước lần tiếp theo.
- OK là cái–trỏ chạm và ba ngón còn lại duỗi. Nếu OK được gán, cần xác nhận
  tư thế ba ngón trước lúc chạm và dành chuỗi đó cho OK; các pinch khác cho drag.
  Đây là phương án thử: không thể phân biệt hai ý định khi toàn bộ tư thế và
  chuyển động giống nhau. Không bật quy tắc mới nếu khiến drag khó bắt hơn.
- Bốn góc thuộc màn hình điều khiển đang chọn, dùng tọa độ thật kể cả màn hình
  có tọa độ âm. Vào vùng góc rồi nắm–thả hai lần trong khoảng thời gian giới hạn.
- Ở hotcorner đã cấu hình, chuỗi fist dành cho hotcorner, không đồng thời
  switch hai tay; rời góc hoặc timeout hủy. Fist vẫn nhả nút chuột an toàn.
- Dùng chung trình gán hành động: tổ hợp phím và danh sách hành động hệ thống
  có adapter hỗ trợ. Không hứa sao chép mọi chức năng Hot Corners của macOS;
  mục chưa hỗ trợ trên nền tảng phải hiện rõ, không im lặng thất bại.

Nghiệm thu: symbol không lặp khi giữ, OK không thành drag, double fist không
kích hoạt hai chức năng, kiểm tra cả ba màn hình và lưu/mở lại Settings.

## Giai đoạn 5 — Zoom và âm lượng

- Thu video mẫu ngắn trước khi chốt hình học: nghỉ → động tác → nghỉ, vài lần
  mỗi chiều, thêm các động tác gần giống nhưng không có ý định kích hoạt.
- Zoom giữ chiều yêu cầu: xòe → chụm là zoom in; chụm → xòe là zoom out.
  Chỉ xét biến đổi độ mở tương đối, không nhầm đưa tay gần camera với zoom.
- Volume: năm ngón hướng camera hơi chụm, xoay thuận/ngược kim đồng hồ tăng/giảm.
  Chốt quy ước chiều theo preview ảnh gương, xử lý góc qua ±180 độ, dead zone,
  bước âm lượng và giới hạn tốc độ; không phản ứng với xoay nhỏ vô ý.
- Phân xử từ tư thế khởi đầu và chuyển động chủ đạo; vào zoom/volume rồi thì
  không chuyển sang scroll/pinch giữa chừng. Trường hợp không đủ phân biệt sẽ
  đề xuất dấu hiệu vào chế độ rõ hơn trước khi đổi yêu cầu người dùng.
- Adapter định nghĩa hành động zoom và volume riêng. Zoom cần kiểm chứng theo
  ứng dụng (trình duyệt, ảnh, tài liệu), không coi Ctrl+wheel là hỗ trợ mọi app.

Nghiệm thu: đúng chiều, không nhảy nhiều bước, không click/cuộn phụ; thử các
ứng dụng đích và các tư thế chuyển tiếp, không chỉ video mẫu đúng chuẩn.

## Giai đoạn 6 — Giao diện, hiệu năng và nghiệm thu toàn bộ

- Settings gộp: Mouse / Second hand / Symbols & Corners / Recognition.
  Gesture guide ngắn gọn phản ánh cấu hình thật; toggle Guide/Skeleton/Debug.
  Status hiển thị trạng thái đang chờ, tiến độ và lý do không nhận khi cần.
- Benchmark cùng camera 720p30, ánh sáng và chuỗi tay; so sánh Debug Off/On.
  Báo FPS nhận diện, tuổi frame, thời gian xử lý p50/p95 và input events.
  Độ trễ tay–màn hình cần quay tham chiếu, không suy ra từ FPS hoặc log nội bộ.
- Kiểm tra đồng thời hai tay: modifier + click/drag/scroll; chuyển mode khi đang
  giữ phím; mất tracking; camera lỗi; Settings; Pause; thoát; ba màn hình.
- Windows kiểm thử thực tế trước; macOS kiểm thử trên máy thật trước khi công bố
  tương thích. Không build exe trước mỗi vòng test; đóng gói sau nghiệm thu.

## Kiểm tra bắt buộc cho từng giai đoạn

```powershell
$env:PYTHONPATH='src'
.\.venv311\Scripts\python.exe -m unittest discover -s tests -v
.\.venv311\Scripts\python.exe -m compileall -q src tests scripts
git diff --check
```

Camera smoke phải bắt đầu Pause. Ghi kết quả đạt/chưa đạt và giới hạn vào
`docs/development-status.md`, cập nhật handoff và guide mỗi giai đoạn.
Chưa cần người dùng cung cấp ảnh/video để bắt đầu giai đoạn 1–2; yêu cầu mẫu
cụ thể khi kiểm chứng OK/drag và trước khi chốt zoom/volume.

## Theo dõi

- [x] 1. Phân xử + schema + replay (code thử nghiệm)
- [x] 2. Hai tay + Ctrl/Shift/Alt + mapping (code thử nghiệm)
- [x] 3. Cuộn dọc/ngang (code thử nghiệm)
- [x] 4. Symbol + hotcorner (code thử nghiệm)
- [x] 5. Zoom + âm lượng (code thử nghiệm)
- [ ] 6. Nghiệm thu + tài liệu + đóng gói

134 tests qua, camera smoke ở Pause thành công. Giai đoạn 6 đã có tài liệu,
kiểm tra UI và đo hiệu năng; chưa nghiệm thu cử chỉ với người dùng, macOS hay
đóng gói. Các dấu hoàn thành trên chỉ phản ánh triển khai code, không thay cho
tiêu chí nghiệm thu thực tế. Chi tiết: ../gesture-hand-v1-testing-vi.md.
