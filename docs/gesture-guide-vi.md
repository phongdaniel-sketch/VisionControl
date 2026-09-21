# Bảng cử chỉ VisionControl

**Bản hiện tại đã bật Gesture Hand v1 thử nghiệm.** Xem bảng đầy đủ và cách
gán hành động tại [Hướng dẫn thử v1](gesture-hand-v1-testing-vi.md).
Ctrl/Shift/Alt 1 giây, cuộn, zoom, volume, symbol và hotcorner đã có code;
mapping v1 mặc định trống. Các bảng bên dưới là lịch sử cơ chế cũ khi tắt v1.

## Chế độ hiện tại: Thumb lock + curl clicks

Đã chọn trong Settings → Mouse → Pointer mode. Cập nhật 06/09/2026.

Skeleton: On hiển thị ngón trỏ I8 màu vàng và ngón cái T4 màu xanh cyan,
không cần bật Debug. Đây là vị trí mô hình ước lượng, không phải bảo đảm
đầu ngón đã được nhận đúng khi các ngón che nhau.

### Tay trái: bàn phím (cấu hình hiện tại)

| Cử chỉ | Phím / thao tác |
| --- | --- |
| Duỗi ngón trỏ | W |
| Duỗi trỏ + giữa | A |
| Duỗi trỏ + giữa + áp út | D |
| Duỗi bốn ngón, khép ngón cái | S |
| Mở cả năm ngón | Space |
| Nắm tay | Không còn bật/tắt ARMED; giữ Ctrl theo yêu cầu mới chưa triển khai |

Phím chỉ được phát khi app ACTIVE; cơ chế ARMED bằng nắm tay đã bỏ. Đổi phím hoặc kiểu
nhấn/giữ tại Settings → Gestures → Keyboard hand. Trong Thumb lock, các
thao tác chuột bên dưới được cố định trong code; chưa có trình tạo cử chỉ mới.
Để thêm cử chỉ, cần xác định tay, tư thế bắt đầu, chuyển động, hành động,
điều kiện kết thúc/hủy và cách tránh trùng với click/drag hiện có.

### Tay phải: chuột

| Thao tác tay điều khiển chuột | Kết quả |
| --- | --- |
| Khép ngón cái, giữ tay nhìn rõ | Con trỏ theo đầu ngón trỏ; không xét tư thế ba ngón còn lại |
| Mở ngón cái | Khóa con trỏ; chờ trạng thái **Locked** trước khi click |
| Khi khóa: duỗi ngón trỏ, co rồi duỗi lại | Click trái một lần |
| Mở cái: duỗi trỏ + giữa, co đồng thời rồi duỗi lại cả hai | Click giữa một lần |
| Tách cái khỏi trỏ/giữa trước, rồi chạm đầu ngón cái với đầu ngón giữa | Click phải ngay lúc chạm; giữ không lặp; tách ra để click tiếp |
| Chỉ co rồi duỗi riêng ngón giữa | Không phát click |
| Tách hai đầu ngón cái–trỏ; chụm và giữ | Giữ chuột trái để drag, không cần khóa trước |
| Đang giữ pinch: di chuyển lòng bàn tay | Kéo tương đối từ vị trí bắt đầu, không nhảy về đầu ngón trỏ |
| Tách ngón cái–trỏ | Nhả chuột, kết thúc drag |
| Nắm hoàn toàn và khép ngón cái / Pause / mất tay | Dừng và nhả nút chuột |

Các click được phát khi duỗi lại sau khi co, không phải ngay lúc bắt đầu co.
Co hai ngón gần đồng thời (trong khoảng 120 ms), giữ co ít nhất 60 ms và hoàn tất
chu kỳ trong 800 ms. Giữ nguyên ngón đang co không tạo click lặp.
Pinch chỉ cần hai đầu ngón cái–trỏ tách trước, rồi chụm ổn định khoảng 0,1 giây
để bắt đầu drag. Không bắt buộc duỗi thẳng ngón trỏ hoặc chụm trong 0,8 giây.
Khi kéo, tách hai đầu ngón ổn định 0,1 giây để nhả; một khung hình nhiễu chưa
làm nhả. Trong lúc xác nhận thả, con trỏ tạm đứng yên. Mất tay/Pause vẫn nhả ngay.
Sau mất tay, tách rồi chụm lại để bắt đầu một lần kéo mới. Chỉ mở ngón cái không tự phát click phải.

Chế độ này không dùng Peace để cuộn hoặc pinch ngón giữa để click phải.
Cấu hình phím tay trái giữ nguyên. Đây là chức năng vừa triển khai, cần thử bằng
tay thật để cân chỉnh; không bảo đảm nhận đúng khi landmark bị che khuất.

## Bảng cũ: Index fingertip (tham khảo)


Cập nhật: 05/09/2026. Bảng phản ánh cấu hình hiện tại: tay phải điều khiển chuột, tay trái điều khiển bàn phím, chế độ con trỏ **Index fingertip**.

| Cử chỉ | Cách thực hiện | Tay phải hiện tại | Tay trái hiện tại |
| --- | --- | --- | --- |
| **Point** | Duỗi riêng ngón trỏ; các ngón còn lại co tự nhiên | Di chuyển con trỏ | Nhấn `W` |
| **Peace** | Duỗi ngón trỏ + ngón giữa | Di chuyển tay lên/xuống để cuộn | Nhấn `A` |
| **Three fingers** | Duỗi ngón trỏ + ngón giữa + ngón áp út | Chưa gán | Nhấn `D` |
| **Four fingers** | Duỗi bốn ngón, khép ngón cái | Chưa gán | Nhấn `S` |
| **Open palm** | Mở cả bàn tay, ngón cái mở | Chưa gán | Nhấn `Space` |
| **Fist** | Nắm tay | Dừng con trỏ, nhả nút chuột | Giữ 1 giây để bật/tắt điều khiển bàn phím |
| **Pinch index** | Duỗi ngón trỏ trước, rồi chụm đầu ngón cái + ngón trỏ | Click trái; giữ để kéo | Chưa hỗ trợ gán phím |
| **Pinch middle** | Giơ ngón giữa trước, rồi chụm với ngón cái | Click phải | Chưa hỗ trợ gán phím |

## Khi sử dụng

- Các phím của tay trái chỉ được gửi khi Controller đang Resume và điều khiển bàn phím đã **ARMED**. Nắm tay trái khoảng 1 giây, rồi thả ra trước khi thực hiện cử chỉ tiếp theo.
- Với pinch, mở ngón cái cách ngón dùng để click trước khi chụm. Sau mỗi lần click, tách các ngón ra để chuẩn bị lần tiếp theo.
- Khi trỏ, có thể hơi cong ngón trỏ và co tự nhiên các ngón còn lại. Giữ đầu ngón trỏ nhìn thấy rõ trong camera; ngón bị che có thể nhận sai.
- Bảng này là bản ghi cấu hình tại ngày cập nhật, không tự thay đổi khi bạn sửa Settings.

## Phím tắt của cửa sổ Controller

| Phím | Chức năng |
| --- | --- |
| `Space` hoặc `P` | Pause/Resume khi cửa sổ Controller đang được chọn |
| `C` | Bắt đầu calibrate |
| `Space` trong lúc calibrate | Chốt vị trí cạnh hiện tại, không Pause/Resume |
| `R` | Hủy calibrate, giữ calibration trước đó |

Trong lúc calibrate, app tạm dừng điều khiển chuột và bàn phím. Các cạnh được chốt theo thứ tự **trái → phải → trên → dưới**, tính theo hình camera. Hoàn tất bốn cạnh hợp lệ sẽ lưu calibration trên máy.

## Xem và chỉnh cấu hình

- Trong app: **GESTURE GUIDE** để xem hướng dẫn; **Settings → Gestures** để chỉnh cử chỉ.
- [Cấu hình người dùng hiện tại](../data/user_profile.json): phím được gán, vai trò hai tay, chế độ con trỏ và ngưỡng nhận diện.
- [Nội dung hướng dẫn trong source](../src/vision_control/controller_labels.py).
- [Logic nhận diện cử chỉ](../src/vision_control/gestures.py).

File này dùng để tham khảo. Chỉnh nội dung bảng không thay đổi hành vi của app; hãy đổi trong Settings.

## Xem vùng calibration và quay debug

- **Show calibration area**: bật/tắt khung xanh và đường tâm của vùng calibration đã lưu trên hình camera.
- **Debug recording**: tạm dừng Controller và mở cửa sổ debug. Bấm **Bắt đầu ghi 30 giây** để ghi webcam + vùng con trỏ mô phỏng. Đóng cửa sổ debug để trở về Controller paused.
- Hoặc đóng app đang dùng camera, rồi chạy `./scripts/windows.ps1 diagnose -CameraIndex 0`.
- Dữ liệu được lưu tại `data/captures/`. Debug không ghi desktop hoặc âm thanh, không điều khiển chuột Windows thật.

Vùng calibration không giới hạn nơi camera nhận diện tay. Nó ánh xạ tọa độ đầu ngón trỏ trong ảnh sang **màn hình đang chọn**: góc trái trên sang góc trái trên, tâm sang tâm, góc phải dưới sang góc phải dưới. Ra ngoài vùng thì tọa độ đích bị giới hạn ở mép màn hình. Điều kiện cử chỉ, làm mượt và khóa khi pinch vẫn có thể khiến con trỏ chưa tới ngay tọa độ đích.

**Processing FPS** là tốc độ hoàn tất vòng xử lý/hiển thị, không phải thông số FPS tối đa của webcam. Các số Camera read / Tracking / Runtime giúp xác định bước chậm; Camera read không đo được độ trễ bên trong cảm biến hoặc bộ đệm driver.

Preview đánh dấu **I8** (vàng) là đầu ngón trỏ, **T4** (xanh cyan) là đầu ngón cái.
