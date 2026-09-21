# Nghiệm thu điều khiển cử chỉ VisionControl

Ngày lập: 2026-09-19. Đối chiếu mã nguồn hiện tại, không phải exe đã build.

## Kết quả hiện có

- Đã chạy `scripts/windows.ps1 test`: 162/162 test giả lập đạt; compileall và git diff --check đạt.
- Chưa thử camera, bàn tay thật, phát input thật hoặc đo độ trễ trong đợt kiểm tra này.
- Bản sửa Palm curl-click ngày 19/9 cần ưu tiên nghiệm thu với scroll/zoom/volume bật.
- Test giả lập chứng minh hành vi với landmark được cung cấp; không chứng minh camera nhận đúng tay ngoài thực tế.
- README và phần đầu gesture-hand-v1-testing-vi.md có mô tả lịch sử. Dùng guide hiện tại và phần cập nhật mới nhất trong workspace-handoff.md.

## Chuẩn bị

1. Lưu công việc, dùng tài liệu thử và thư mục rỗng. Có chuột/bàn phím thật để Pause hoặc Quit.
2. Chạy từ source để có bản sửa mới nhất; chọn camera vật lý trong Settings, không mặc định index 0 luôn đúng.
3. Ghi OS, phiên bản camera, FPS/resolution thực tế, màn hình/DPI, ánh sáng, khoảng cách tay, commit và thay đổi local. Không coi preset 720p30 là số đo FPS thực tế.
4. Sao lưu profile/calibration vào thư mục kết quả cá nhân. Profile source và profile exe có thể khác nhau: exe Windows dùng %LOCALAPPDATA%\VisionControl.
5. Profile source được đọc trong đợt này: Palm, tay chuột Right, tay phụ Left, swap_hands=true, màn hình fixed/0; two_hands/scroll/zoom/volume bật; fist_switch tắt. Kiểm tra vai trò tay trong preview trước Start.
6. Symbol, corners và bindings 1–5 trong gesture_v1 đang trống. Mapping cũ left_hand không phải mapping v1 đang hoạt động. Mục chưa gán đánh dấu BLOCKED hoặc N/A có lý do, không đánh dấu PASS.
7. Calibrate riêng Palm và Index fingertip. Sau Save/Calibrate ứng dụng phải ở Pause; bấm Start khi sẵn sàng.
8. Escape chỉ ẩn Controller vào tray; Active vẫn điều khiển. Dừng bằng Pause; thoát bằng Quit/đóng cửa sổ. Không dùng Escape làm nút dừng khẩn cấp.

Mở source từ PowerShell:

```powershell
Set-Location 'D:\Phong Bo Bo\Jobs\Dev\VisionControl'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows.ps1 run -CameraIndex 0
```

## Quy tắc chạy và đo

Mỗi lượt: nghỉ 2 giây -> chuẩn bị -> động tác -> nhả -> nghỉ. Lượt không nhận vẫn tính vào tổng. Làm 3 block x 20 lượt cho mỗi lệnh cốt lõi ở chế độ chính; nghỉ 2 phút giữa block. Chế độ phụ kiểm tra 10 lượt/lệnh trước, chỉ tuyên bố hỗ trợ ổn định sau đủ 60 lượt như chế độ chính.

Ghi một dòng mỗi lượt vào CSV kèm theo. Correct, Miss, Wrong, Duplicate là bốn kết quả loại trừ nhau; nếu nhiều lỗi cùng lượt, ghi lỗi nặng nhất vào outcome và tất cả sự kiện vào actual_events. Stuck là lỗi riêng, luôn chặn nghiệm thu. Đếm Wrong/Duplicate dù cuối lượt vẫn có lệnh đúng.

Ngưỡng sau là mục tiêu nghiệm thu đề xuất, không phải kết quả đã đo:

- Lệnh rời rạc: >=57/60 lượt đúng cho T03–T05 và >=57/60 drag hoàn tất cho T07, từng loại riêng; không gộp để che lỗi.
- Không kẹt nút/phím trong bất kỳ bài nào. Bất kỳ lần kẹt nào: dừng nghiệm thu, lưu bằng chứng, sửa và thử lại.
- Không có lệnh ngoài ý muốn trong 10 phút vận động thông thường; báo cáo '0/10 phút', không suy ra không bao giờ lỗi.
- Click mục tiêu 48 px: >=57/60 trúng, không click đôi ngoài ý muốn. Mục tiêu 24 px là bài nâng cao, ghi riêng.
- Giữ con trỏ 10 giây x10: mục tiêu dao động trong bán kính 8 px quanh vị trí đầu, cùng DPI, đo màn hình; ghi drift cực đại.
- Độ trễ P95 phần xử lý <=300 ms sau khi đã đủ điều kiện xác nhận cử chỉ. Ghi cả độ trễ tổng để phản ánh cảm giác sử dụng.
- Modifier có thời gian giữ 1 giây; symbol mặc định 0,5 giây; pose 0,3 giây; pinch vào/ra 0,1 giây. Không áp ngưỡng 300 ms lên toàn bộ thời gian giữ có chủ đích này.
- Nhả input khi Pause/mất tay: mục tiêu thực tế <=500 ms. Đo từ thao tác Pause hoặc tay rời khung đến sự kiện nhả; ghi nếu chỉ có thể đo gián tiếp.

Quay điện thoại 60 fps trở lên chứa đồng thời bàn tay và màn hình để đo end-to-end, đồng thời ghi FPS quay. Độ phân giải thời gian 60 fps xấp xỉ 16,7 ms. Với 60 mẫu hợp lệ, P95 nearest-rank là mẫu thứ 57 sau sắp tăng dần. Lượt không phản hồi ghi Miss, không loại khỏi tỷ lệ thành công và không gán latency=0. FPS Debug recorder không đại diện FPS Controller.

## Test case theo chức năng

| ID | Ưu tiên | Cách thực hiện | Kết quả cần quan sát / số lượt |
|---|---|---|---|
| T01 | P0 | Mở app, đưa cả hai tay vào, mở Settings rồi Save | Không phát input trước Start; Save trở về Pause; 10 lần |
| T02 | P0 | Palm: mở/khép cái và di chuyển. Index: cái khép di chuyển, cái mở khóa | Đúng khác biệt hai mode, không nhảy khi chuyển; 10 chu kỳ/mode |
| T03 | P0 | Palm, cái mở: chuẩn bị trỏ duỗi, co trỏ rồi duỗi lại | Đúng 1 click trái sau chu kỳ, không scroll/zoom/volume; 60 lượt với tất cả motion bật |
| T04 | P0 | Như T03 nhưng co rồi duỗi đồng thời trỏ+giữa | Đúng 1 click giữa, không click trái/phải; 60 lượt |
| T05 | P0 | Tách cái khỏi trỏ/giữa, rồi chạm đầu ngón cái với ngón giữa | Đúng 1 click phải ngay lúc chạm, giữ không lặp, không cần chờ thả; 60 lượt; thử thêm tiếp xúc cả ba ngón để xác nhận không click nhầm |
| T06 | P1 | Lặp T03–T05 ở Index fingertip, con trỏ khóa | Click đúng loại tại điểm ngắm; 10/lệnh ban đầu, 60 để nghiệm thu mode này |
| T07 | P0 | OK chưa gán: tách cái–trỏ, pinch đủ 100 ms, kéo bằng lòng bàn tay, tách đủ 100 ms | 1 mouse-down, kéo liên tục, 1 mouse-up; 60 lượt, có kéo chậm/nhanh/chéo |
| T08 | P0 | Đưa bàn tay đã pinch vào camera; pinch cực ngắn rồi thả | Không tự bắt đầu drag khi thiếu chuẩn bị hoặc thiếu thời gian; 20 mỗi loại |
| T09 | P0 | Gán OK vào thao tác vô hại; cái–trỏ chạm và 3 ngón còn lại duỗi. Sau đó thử drag với 3 ngón co nhẹ | OK được ưu tiên khi đã gán; drag đang chạy không bị OK chiếm; 20 mỗi nhánh |
| T10 | P0 | Cái mở, 4 ngón duỗi sát: cuộn dọc, ngang; thử curl khi đang cuộn; rời tư thế rồi click | Giữ trục cuộn đến khi thoát; không click khi scroll đang sở hữu thao tác; thoát xong click lại được; 20/trục |
| T11 | P1 | Xòe rộng -> chụm và ngược lại trong trình duyệt hỗ trợ Ctrl+=/- | Zoom đúng hai chiều, nghỉ không lặp; 20/chiều; reset zoom giữa block |
| T12 | P0 | Đầu ngón hướng camera, 4 ngón duỗi và cái–trỏ tách rõ; xoay, rồi chuyển sang pinch kéo | Volume đúng chiều theo preview; không chiếm drag; 20/chiều và 20 chuyển tiếp; dùng mức âm lượng thấp |
| T13 | P0 | Tay phụ fist 1s / 5 ngón duỗi sát gồm cái 1s / pinch 1s; nhả từng tư thế | Ctrl / Shift / Alt đúng; thả là nhả; 20 từng modifier. Không dùng quy tắc fist ARMED cũ |
| T14 | P1 | Gán lần lượt 1–5 ngón vào ký tự vô hại trong tài liệu thử, thử Press rồi Hold | Press không lặp khi giữ; Hold nhả khi thoát. Năm ngón mapping phải xòe rộng, không nhầm Shift; 20/mapping/type |
| T15 | P1 | Gán từng thumbs up/down/OK/victory, giữ 5s, nhả và làm lại | Một lần mỗi lần giữ; đủ symbol_seconds; không cướp click/drag; 20/symbol |
| T16 | P1 | Gán một hotcorner, vào góc và nắm–thả hai lần; thử 1 lần, sai góc, quá cửa sổ 2,5s | Chỉ chuỗi hợp lệ kích hoạt 1 lần; 20 hợp lệ + 10 mỗi nhánh âm tính |
| T17 | P1 | fist_switch tắt: giữ fist chuột >3s; bật tùy chọn rồi thử lại | Khi tắt không toggle; khi bật 1 toggle/hold, thả rồi mới toggle lại; 10 mỗi nhánh |
| T18 | P0 | Khi đang drag hoặc giữ modifier: lần lượt Pause, mất tay, mở Settings, Calibrate, Quit | Nhả mọi nút/phím; không kéo tiếp hoặc còn Ctrl/Shift/Alt sau đó; 5 lần cho mỗi tổ hợp thao tác đang giữ và cách dừng |
| T19 | P0 | Đang drag/giữ modifier: che camera, rút webcam; nối lại | Không kẹt input, có trạng thái lỗi/phục hồi rõ; không chạy lệnh cũ khi khôi phục; 5/nhánh |
| T20 | P0 | Active -> Esc ẩn -> mở lại; Pause -> ẩn -> mở lại -> Start; đóng cửa sổ | Active ẩn vẫn hoạt động; Paused ẩn nhả input và giải phóng camera; mở lại vẫn Pause; đóng cửa sổ thoát, icon mất; 10 chu kỳ |
| T21 | P0 | Đưa tay ra/vào mép, che một phần, hai tay bắt chéo, người khác đưa tay vào | Không click/chord ngoài ý muốn; mất theo dõi phải nhả; 20 mỗi tình huống |
| T22 | P0 | Click 60 mục tiêu 48 px ở 9 vị trí, giữ yên 10s x10, kéo thả 20 đối tượng | Ghi hit rate, jitter, drift, jump và mỏi tay; phân biệt nhận đúng click với click trúng mục tiêu |
| T23 | P1 | Fixed/all/active với 2 màn hình; active giữ biên rồi rời biên | Fixed không tự đổi; active chỉ đổi sau dwell và không lặp khi giữ; all đúng tọa độ; 10/nhánh; 1 màn hình ghi N/A |
| T24 | P0 | Gõ phím, uống nước, chạm mặt, trò chuyện, nghỉ tay khi app Active | 10 phút không thao tác chủ ý: đếm mọi lệnh nhầm, không chỉ click |
| T25 | P1 | Dùng 45 phút; so đầu/giữa/cuối; lặp khi Unity đang chạy | Ghi FPS Controller, latency, CPU/RAM, lỗi và mức mỏi; không tích lũy lag/kẹt phím; không ép mở thêm tải khi máy đã quá tải |

## Kế hoạch thực tế cho người dùng

### Buổi 1: 15 phút sàng lọc, sau đó 45–60 phút baseline

Chạy T01/T02/T18/T20 trước, 5–10 lượt. Nếu còn kẹt phím hoặc không Pause được thì dừng. Tắt scroll/zoom/volume và để OK trống, chạy 10 lượt T03–T07 để học tư thế. Sau đó bật lại cả ba và chạy 3 block x20 cho từng click và drag. Kết quả tắt chức năng chỉ dùng cô lập lỗi, không được thay thế kết quả đầy đủ.

### Buổi 2: 45–60 phút, tương tác giữa các nhóm

Chạy T09–T17, T19, T21. Chỉ gán một symbol/hotcorner một lúc. Modifier thử riêng rồi kết hợp Ctrl+click, Shift+click trên tài liệu thử. Mỗi lần lỗi lưu clip gồm 2 giây trước chuẩn bị và 2 giây sau nhả. Không chỉnh ngưỡng giữa block; đổi ngưỡng là bắt đầu session mới.

### Buổi 3: môi trường, chia nhiều block có nghỉ

Lặp T03/T05/T07/T13/T24 ở điều kiện baseline sáng đều, ánh sáng yếu, ngược sáng, nền rối, khoảng cách gần/vừa/xa (ghi cm thực tế), tay ở giữa/mép và thay góc cổ tay. Chỉ đổi một yếu tố mỗi block. Sàng lọc 10 lượt; mỗi điều kiện muốn công bố hỗ trợ phải kiểm tra đủ mẫu và tiêu chí như baseline. Điều kiện thất bại phải được ghi là giới hạn hoạt động.

### Buổi 4: sử dụng thật và người mới

Chạy T22/T25. Mời 3–5 người, mỗi người 2 phút hướng dẫn và 10 phút thực hiện cùng chuỗi: trỏ vào mục tiêu -> click -> kéo thả -> cuộn -> zoom -> giữ/nhả modifier -> Pause. Ghi tỷ lệ hoàn thành, thời gian, số cần trợ giúp, lệnh nhầm, mức mỏi 0–10. Không suy rộng kết quả một người thành mọi người dùng. Nếu quảng bá cả Palm và Index, thực hiện mỗi mode với calibration riêng và đảo thứ tự thử giữa người dùng.

## Thu bằng chứng và phát lại

Settings -> Preview & Debug -> Save & open Debug recording; bấm Start trong cửa sổ ghi. Debug dùng adapter giả, không phát input OS thật; do đó cần vòng Controller thực tế riêng để xác nhận thao tác trong ứng dụng. Video/landmarks giữ local. Sao lưu đúng profile dùng lúc ghi, ghi nhãn ý định và mốc thời gian, không chỉ dựa nhãn model dự đoán.

```powershell
Set-Location 'D:\Phong Bo Bo\Jobs\Dev\VisionControl'
$env:PYTHONPATH='src'
.\.venv311\Scripts\python.exe scripts/replay_gesture_v1.py 'PATH_TO_frames.jsonl' 'PATH_TO_session_profile.json'
```

Replay không điều khiển PC và không mô phỏng toàn bộ vòng đời camera/tray/UI. Dùng clip lỗi làm bằng chứng nhận diện, replay để truy chuỗi trạng thái, rồi thêm test hồi quy cho lỗi đã tái hiện. Không lấy video cũ để xác nhận camera hiện tại nếu phần perception hoặc môi trường đã đổi.

## Ghi kết quả và quyết định

Copy mẫu CSV vào data/acceptance/<session>/results.csv, lưu profile/calibration và clip cạnh đó; không commit dữ liệu cá nhân. Mỗi session thêm notes.txt ghi cấu hình môi trường, commit + dirty state, số đo thực tế và các thay đổi ngưỡng.

Ưu tiên lỗi: P0 kẹt phím/nút, không dừng được, lệnh sai/nhầm hoặc lỗi thao tác cốt lõi; P1 các chức năng bổ sung và chất lượng; P2 hiển thị/hướng dẫn. Nghiệm thu khi không còn P0 chưa xử lý, từng chức năng đạt ngưỡng, test hồi quy đạt và điều kiện hỗ trợ được ghi rõ. BLOCKED/NOT_RUN không tính PASS; mọi N/A phải có lý do.

Lỗi cần gửi lại: ID test + mode + profile + expected/actual + số lần tái hiện/tổng lượt + timestamp clip + thao tác phục hồi. Chỉ tinh chỉnh một nhóm tham số ở Gestures > Fine tuning mỗi vòng; chạy lại ca lỗi, ca gần giống âm tính và T18 trước khi chấp nhận thay đổi.
