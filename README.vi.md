# TTS Broadcast

**[Tiếng Việt]** | **[English](./README.md)**

Một integration tùy chỉnh Home Assistant để phát thông báo TTS (nối tiếng) đến nhiều loa cùng lúc. Chọn loa qua các công tắc, dùng chung thanh trượt âm lượng, kích hoạt bằng giọng nói qua Assist, và điều khiển bằng bảng thang card — hoàn toàn cục bộ, không phụ thuộc đám mây của chính nó.

> **Lưu ý:** Kho lưu trữ hiện đang ở trạng thái RIÊNG TƯ. Cho đến khi công khai, hãy cài đặt thủ công bằng cách sao chép thư mục (xem mục Cài đặt). Đừng tự thay đổi chế độ công khai/repository; xem `PUBLISH_CHECKLIST.md` để biết quy trình phát hành.

## Integration này là gì và tại sao dùng

TTS Broadcast giúp bạn phát một thông báo trên nhiều loa cùng một lúc. Trường hợp phổ biến là thông báo tiếng Việt như "thông báo, cơm chín rồi" (cơm đã chín). Bạn cấu hình một hoặc nhiều loa media_player, chọn những loa nào đang bật, thiết lập âm lượng chung, và nói hoặc gõ tin nhắn qua Assist.

## Các tính năng và những việc integration YÊU CẬU LÀM

**Các tính năng**

- Thông báo một tin nhắn đến nhiều loa cùng lúc.
- Công tắc bật/tắt từng loa (chỉ loa đang bật mới phát).
- Thanh trượt âm lượng chung ("Âm lượng ban đầu" chỉ là giá trị khởi đầu trước khi thanh trượt có trạng thái lưu).
- Kích hoạt bằng giọng nói qua Assist: một câu lệnh như "thông báo {message}" chỉ được phát đến những loa đang bật.
- Bảng thang card tùy chỉnh (`tts-broadcast-card`) với công tắc từng loa, âm lượng, tin nhắn, các nún Phát/Dừng/Chọn tất cả/Chọn không và hàng TALK (Assist) có tên và biểu tượng bản địa hóa.
- Dịch vụ: `tts_broadcast.speak`, `tts_broadcast.stop`,
  `tts_broadcast.get_dashboard_card`, `tts_broadcast.debug_selection`.
- Hoàn toàn cục bộ khi dùng engine TTS cục bộ (ví dụ Wyoming); không phụ thuộc đám mây của chính nó.

**Integration YÊU CẬU LÀM**

- Không luồng giọng nói thực của bạn. Giọng nói được chuyển thành văn bản rồi phát lại bằng TTS.
- Không có âm lượng từng loa (một âm lượng chung).
- Không có giao diện frontend tùy chỉnh ngoài card.
- Không luồng âm thanh giữa các thiết bị.

## Yêu cầu

- Home Assistant **2026.11.0 trở lên** (kiểm tra thời gian chạy thực trên nguồn HA 2026.10.4 / 2026.11; các phiên bản cũ hơn chưa được kiểm tra cục bộ).
- Một TTS entity (ví dụ `tts.wyoming_vietnamese`).
- Các loa `media_player` có thể phát TTS.
- Tùy chọn: một engine STT để kích hoạt bằng giọng nói qua Assist.

## Cài đặt

### Cài thủ công (hoạt động ngay; repository là riêng tư)

1. Sao chép `custom_components/tts_broadcast` vào
   `config/custom_components/tts_broadcast`, hoặc giải nén
   `dist/tts_broadcast.zip` vào `config/custom_components/`.
2. Khởi động lại Home Assistant.
3. Thêm integration từ Settings -> Devices & Services.

### HACS (chỉ sau khi repository công khai)

1. HACS -> Integrations -> Custom repositories.
2. Thêm URL repository này, chọn category "Integration".
3. Cài "TTS Broadcast" và khởi động lại Home Assistant.
4. Thêm integration từ Settings -> Devices & Services.

## Cấu hình

Tất cả cấu hình từ giao diện (Settings -> Devices & Services -> TTS Broadcast -> Configure).

| Trường | Ý nghĩa | Ví dụ |
|--------|---------|---------|
| TTS entity | Engine TTS dùng để nói | `tts.wyoming_vietnamese` |
| Speakers | Các loa media_player có thể phát thông báo | `media_player.phong_khach`, … |
| Speakers without volume control | Các loa được loại trừ khỏi `volume_set` | `media_player.san_vuon` |
| Âm lượng ban đầu | Âm lượng khởi đầu trước khi thanh trượt có trạng thái lưu | `50` |
| Ngôn ngữ / tùy chọn | Ngôn ngữ/tùy chọn tùy chọn truyền cho TTS | `vi` / `{}` |
| Cụm từ bỏ đi | Cụm từ bị gỡ khỏi đầu trước khi phát | `thông báo` |
| Cụm từ giữ nguyên | Cụm từ giữ nguyên cả câu | `xin chào` |
| Yêu cầu cụm từ | Nếu tắt, mọi câu đều được phát | đã bật |
| Agent dự phòng | Agent Assist dùng khi không khớp cụm từ | một conversation agent khác |
| Không phân biệt dấu | Bỏ qua dấu tiếng Việt khi so khớp | đã bật |
| Văn bản trả lời | Xác nhận ngắn trả về Assist | `Đã gửi` |
| Chế độ phát | `per_speaker` (mặc định) hoặc `single_call` | `per_speaker` |
| Kiểm tra tất cả media player | Quan sát mọi media player trong khoảng thời gian kiểm tra | tắt |

Ví dụ cụm từ: bỏ đi `thông báo` nên "thông báo, cơm chín rồi" chỉ phát "cơm chín rồi"; giữ nguyên `xin chào` nên "xin chào mọi người xuống ăn cơm" được phát hết câu.

## Các entity và dịch vụ

Một thiết bị "TTS Broadcast" với một công tắc mỗi loa, một số âm lượng chung, một ô tin nhắn, các nún Phát/Dừng/Chọn tất cả/Chọn không, và một conversation agent.

### `tts_broadcast.speak`

```yaml
service: tts_broadcast.speak
data:
  message: "Cơm chín rồi, mọi người xuống ăn!"
  speakers: ["media_player.phong_khach"]  # tùy chọn
  volume: 70                               # tùy chọn, 0-100
  language: vi                             # tùy chọn
  cache: false                             # tùy chọn
  audit: true                              # tùy chọn, chờ chi tiết kiểm tra
```

Hình dạng phản hồi: `{played, skipped, failed, errors, targeted, unexpected_started,
context_id}`.

- `played`: các loa HA đã chấp nhận yêu cầu — **"đã chấp nhận" không có nghĩa là đã nghe được**.
- `skipped`: các loa không sẵn sàng/không xác định.
- `failed`: các loa bị lỗi.
- `errors`: `{entity_id: văn bản lỗi ngắn}`.
- `targeted`: danh sách chính xác gửi đến `tts.speak`.
- `unexpected_started`: các loa media_player bắt đầu phát nhưng không được mục tiêu
  (chỉ được điền khi `audit: true`; nếu không xem `debug_selection`/diagnostics).

### `tts_broadcast.stop`

```yaml
service: tts_broadcast.stop
data:
  speakers: ["media_player.phong_khach"]  # tùy chọn
```

### `tts_broadcast.get_dashboard_card`

```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

Trả về đoạn YAML cho bảng thang phù hợp (cũng tạo thông báo liên tục khi
`notify: true`).

### `tts_broadcast.debug_selection`

Không có tác dụng phụ, không phát. Trả về trạng thái từng loa, danh sách đã giải quyết
mà một `speak` không tham số sẽ dùng, bất kỳ media player nào liệt kê một loa đã cấu
hình là thành viên nhóm, và kiểm tra lần thông báo gần nhất. Dùng để chứng minh tại
sao có thêm loa phát.

## Thiết lập giọng nói, bước một bước (đọc bẫy trước)

**Bẫy:** đừng dùng pipeline Assist mặc định cho nút TALK. Pipeline mặc định thường
dùng agent LLM/Home Assistant, và HA sẽ điều phối thông báo đến
`assist_satellite.announce` trên TẤT CẢ các vệ tinh Assist — nên mọi loa phát, chứ
 không chỉ những loa bạn đã bật.

1. Settings -> Voice assistants -> Add assistant.
2. Chọn conversation agent: **TTS Broadcast**.
3. Chọn engine STT và engine TTS của bạn.
4. Lưu pipeline. Đừng **đặt làm pipeline mặc định**.
5. Ghi lại id pipeline.

Trong bảng thang card, đặt `assist_pipeline_id` thành id pipeline đó. Hoặc để lại là
`auto` (mặc định): card sẽ tự tìm pipeline có conversation agent là TTS Broadcast.

Nếu không có pipeline nào dùng agent TTS Broadcast, hàng TALK sẽ bị ẩn và một dòng
thông báo bản địa hóa sẽ hiện ra yêu cầu bạn tạo một pipeline.

## Bảng thang card

Thêm card -> TTS Broadcast. Card sẽ tự phát hiện các entity của integration.

Tùy chọn card (tất cả tùy chọn):

| Tùy chọn | Ý nghĩa | Mặc định |
|--------|---------|---------|
| title | Tiêu đề card | `TTS Broadcast` |
| show_volume | Hiện thanh trượt âm lượng | true |
| show_message | Hiện ô tin nhắn | true |
| show_assist | Hiện hàng TALK (Assist) | true |
| assist_pipeline_id | `auto`, `preferred`, `last_used`, hoặc id pipeline cụ thể | `auto` |
| assist_name | Ghi đè nhãn nút TALK | `TALK` / `NÓI` |
| assist_icon | Ghi đè biểu tượng nút TALK | `mdi:microphone` |
| show_select_buttons | Hiện các nún Chọn tất cả / Chọn không | true |

Phép dự phòng YAML (bảng thang phù hợp):

```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

Sau khi cài đặt hoặc cập nhật, hãy làm mới lại trình duyệt (hard refresh) để card
JS được tải lại cache.

Nếu không có pipeline Assist nào dùng agent TTS Broadcast, hàng TALK không được
vẽ và một dòng thông báo bản địa hóa sẽ hiển thị thay thế.

## Gỡ lỗi

| Vấn đề | Cần kiểm tra |
|--------|-------------|
| Mọi loa đều phát khi tôi nói | Bạn đang dùng pipeline Assist mặc định (một agent LLM/Home Assistant điều hướng đến tất cả vệ tinh). Tạo một pipeline riêng có conversation agent = TTS Broadcast và đặt `assist_pipeline_id` thành id của nó. Dùng Developer Tools > Events > `call_service` để xem ai gọi `assist_satellite.announce` hoặc `tts.speak`. |
| Không thấy nún microphone | Pipeline cần một engine STT. Trang trình duyệt phải là HTTPS, hoặc dùng ứng dụng Companion Home Assistant. Hộp thoại chat riêng của conversation agent chỉ là văn bản theo thiết kế. |
| Một số loa yên lặng hoặc không phát | Kiểm tra thanh trượt âm lượng và âm lượng của chính loa. Các loa trong "Speakers without volume control" không nhận `volume_set`. Kiểm tra loa trực tiếp bằng `tts_broadcast.speak`. |
| Có thêm loa phát | Gọi `tts_broadcast.debug_selection` và so sánh `targeted` với `unexpected_started`. Xem quy trình dưới đây. |
| Card không hiện trong bộ chọn | Làm mới trình duyệt (hard refresh) sau khi cài đặt/cập nhật. |
| Lỗi cấu hình | Kiểm tra bản dịch lỗi tùy chọn (ví dụ "Chọn ít nhất một loa"). |
| Dừng không ngắt phát trên một số loa ESPHome | `media_player.media_stop` ngắt phát trên pipeline ESPHome chưa được kiểm tra (xem Giới hạn đã biết). |

### Có thêm loa phát — quy trình chạy

1. Gọi `tts_broadcast.debug_selection` và đọc kết quả.
2. Bật đúng một công tắc ON, gọi `tts_broadcast.speak` với `return_response`,
   và so sánh `targeted` (danh sách chính xác gửi đến `tts.speak`) với
   `unexpected_started`.
3. Nếu `unexpected_started` trống và `targeted` chỉ có một entity nhưng các loa khác
   vẫn phát, nguyên nhân nằm **ngoài integration**: kiểm tra Logbook xem ai bắt đầu
   phát các loa đó, liệt kê các automation/script gọi `tts.speak` hoặc
   `media_player.play_media`, và kiểm tra gói YAML cũ (script `loa_phat_tts`,
   automation "Assist - thông báo ra loa", `input_boolean.loa_*`).
4. Nếu `targeted` có nhiều hơn một entity, hãy gửi toàn bộ kết quả
   `debug_selection`, trạng thái công tắc, và các dòng log của integration.

## Giới hạn đã biết và trạng thái kiểm tra

| Mục | Trạng thái |
|------|-----------|
| Phát từng loa (một loa lỗi không làm chặn các loa khác) | Đã kiểm tra bằng kiểm thử tự động |
| Gọi `tts.speak` một lần cho mỗi loa, song song | Đã kiểm tra bằng kiểm thử tự động |
| Thanh trượt âm lượng là nguồn tin duy nhất | Đã kiểm tra bằng kiểm thử tự động |
| `debug_selection` / kiểm tra / `unexpected_started` | Đã kiểm tra bằng kiểm thử tự động |
| Chọn pipeline Assist tự động trên card | Đã kiểm tra bằng kiểm thử tự động (logic JS qua node --check) |
| Dòng HA 2026.11, các loa media_player ESPHome | Đã kiểm tra trên HA 2026.10.4 của tác giả |
| Pipeline Assist với TTS/STT cục bộ Wyoming | Đã kiểm tra trên HA 2026.10.4 của tác giả |
| Hành vi loa Tapo | Chưa kiểm tra |
| Các engine TTS khác | Chưa kiểm tra |
| Các phiên bản HA khác | Chưa kiểm tra (khai báo tối thiểu 2026.11.0) |
| Ngắt phát thông báo ESPHome qua `media_stop` | Chưa kiểm tra |
| Trình chỉnh sửa giao diện frontend `assist_pipeline` | Chưa kiểm tra trực tiếp (backend đã xác thực) |

## Bảo mật và quyền riêng tư

- Văn bản tin nhắn không bao giờ được ghi log ở mức info.
- Không có viễn thám, không có cuộc gọi mạng ngoài từ integration.
- Bất kỳ ai có thể truy cập pipeline Assist dùng agent TTS Broadcast đều có thể nói trên các loa của bạn — hãy bảo vệ quyền truy cập pipeline của bạn.
- Không liên kết với hay được khuyến khích bởi Home Assistant, Nabu Casa, Tapo/TP-Link, Zalo, hay Google.

## Phát triển

```bash
ruff check .
ruff format --check .
pytest tests
```

Xem `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, và
`PUBLISH_CHECKLIST.md`. Các ảnh chụp màn hình cần thêm được liệt kê ở
`docs/images/README.md`.

Giấy phép: MIT. Xem `LICENSE`.
