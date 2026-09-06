Đánh số thứ tự các thao tác tay như sau:
Tay phải:

1. Move: Khép ngón cái; con trỏ theo đầu ngón trỏ
2. Lock move: Mở ngón cái
3. Left Click:  Khi khóa: co ngón trỏ rồi duỗi lại
4. Right Click: Khi khóa: co đồng thời trỏ + giữa rồi duỗi cả hai
5. Middle Click: Khi khóa: co ngón giữa rồi duỗi lại
6. Drag: Giữ như cũ
7. Scroll up + down: Ngón cái mở; bốn ngón còn lại duỗi và khép sát nhau. Con trỏ khóa; di chuyển tay lên/xuống để cuộn dọc.
8. Scroll left + right: Cùng tư thế cuộn trên; di chuyển tay trái/phải để cuộn ngang.
9. Zoom in: bàn tay mở, 5 ngón xa nhau sau đó chụm lại với nhau
10. Zoom out: 5 ngón tay đang chụm với nhau sau đó mở bàn tay ra
11. Volume Up + Down: 5 ngón tay hướng về phía camera, hơi chụm nhưng không dính vào nhau, xoay theo chiều kim đồng hồ để tăng âm lượng, xoay ngược chiều kim đồng hồ để giảm âm lượng
12. Cho phép gán chức năng hotcorner ở 4 góc màn hình: Đưa con trỏ chuột tới góc màn hình, sau đó nắm tay, thả tay 2 lần để truy xuất chứng năng đã gán trước đó. (Cho phép gán chức năng ở phần setting tương tự như chứng năng hotcorner của Macos)
13. Cho phép gán chức năng cho 4 Symbol tay: Tay biểu tượng Like/Good job/Thumbs up, tay biểu tượng Thumbs down, tay biểu tượng OK, tay biểu tượng victory. Cho gán như chức năng hotcorner ở trên
14. Switch 2nd hand: Có công tắc chế độ hai tay trong Settings. Cử chỉ tay phải nắm 3 giây để chuyển chế độ có tùy chọn bật/tắt riêng trong Settings; nếu bật thì hiển thị countdown.

Tay trái:
Trong mode 2 tay thì tay còn lại có tác dụng như sau:

1. Giữ phím Ctrl: bàn tay còn lại giữ hình tay nắm đấm ổn định 1 giây trước khi nhấn giữ phím.
2. Giữ phím Shift: bàn tay giơ 5 ngón duỗi và khép sát nhau, giữ tư thế ổn định 1 giây. Phân biệt với 5 ngón xòe rời nhau dùng để gán phím.
3. Giữ phím Alt: bàn tay có ngón trỏ và ngón cái chạm nhau ổn định 1 giây.
4. Gán phím chức năng tương ứng với từng ngón tay, tự đặt lại trong setting được. Ví dụ như giơ 1 ngón tương ứng với bấm phím R, giơ 2 ngón tương ứng với bấm phím E, giơ 3 ngón tương ứng với bấm phím W, giơ 4 ngón tương ứng với bấm phím Q, giơ 5 ngón tương ứng với bấm phím F. Mặc định cứ để trống không gán phím.

## Làm rõ sau trao đổi ngày 06/09/2026

- Đây là yêu cầu cho bản tiếp theo, chưa phản ánh toàn bộ code đang chạy.
- Ngưỡng 1 giây là thời gian xác nhận trước khi nhấn giữ Ctrl/Shift/Alt;
  không phải thời gian chờ nhả phím. Khi rời tư thế thì nhả; Pause, mất tay,
  tắt chế độ hai tay, thoát hoặc lỗi phải nhả phím. Không phát phím số ngón
  trong lúc chờ xác nhận modifier. Ngưỡng click/drag hiện tại không bị đổi.
- OK: cái–trỏ chạm nhau, ba ngón còn lại duỗi. Người dùng đồng ý thử cách
  phân biệt này. Cách phân xử OK với pinch drag cần kiểm chứng trước khi
  triển khai; không được tự biến một lần drag đang diễn ra thành OK.
- Video tham chiếu phù hợp cho zoom, cuộn và xoay âm lượng; ảnh tĩnh phù hợp
  cho tư thế OK, Shift và các symbol. Chưa yêu cầu ghi hình ngay; dữ liệu
  tham chiếu giữ cục bộ, không tự tải lên hoặc tự huấn luyện mô hình.

### Đề xuất triển khai cần kiểm chứng

- Cử chỉ nắm tay chuyển chế độ hai tay mặc định Off, người dùng chủ động bật.
- Hiển thị tiến độ 1 giây cho modifier; chỉ nhận một hành động trên mỗi tay
  tại một thời điểm. Trong lúc drag không kích hoạt cuộn, zoom hay symbol.
- Xác nhận tư thế cuộn trước, rồi dùng hướng dịch chuyển để chọn trục;
  không phát click trong một thao tác cuộn đang diễn ra.
- Thay cơ chế nắm tay trái 1 giây để ARMED của bản cũ khi triển khai chế độ
  mới, vì cùng tư thế này nay dùng giữ Ctrl. Không để hai hành động cùng chạy.
- Chưa chốt ngưỡng phân biệt độ khép/xòe, góc xoay và cách phân xử zoom với
  âm lượng; cần đối chiếu video thao tác, không suy ra từ một ảnh đơn lẻ.

## Quyết định: bỏ ARMED bằng nắm tay trái

Người dùng yêu cầu bỏ hoàn toàn cử chỉ nắm tay trái 1 giây để bật/tắt ARMED.
Không giữ lại như một lựa chọn trong Settings. Profile cũ bật arming cũng phải
bỏ qua cờ này. Nắm tay phải 3 giây để switch 2nd hand là chức năng riêng trong
kế hoạch mới. Giữ Ctrl/Shift/Alt 1 giây chưa triển khai ở bước loại bỏ ARMED này.
