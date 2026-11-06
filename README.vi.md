# TTS Broadcast

Custom integration cho Home Assistant để phát thông báo TTS đến nhiều loa.

## Cài thủ công (repo private)
1. Copy `custom_components/tts_broadcast` vào `config/custom_components/tts_broadcast`, hoặc giải nén `dist/tts_broadcast.zip` vào `config/custom_components/`.
2. Restart Home Assistant.
3. Thêm integration trong Settings -> Devices & Services.

## Cài qua HACS (chỉ khi repo public)
1. HACS -> Integrations -> Custom repositories.
2. Thêm URL repo, chọn category Integration.
3. Cài "TTS Broadcast" và restart Home Assistant.
4. Thêm integration trong Settings -> Devices & Services.

## Cấu hình
Toàn bộ cấu hình qua UI.

## Entities
Một device "TTS Broadcast" với switch từng loa, volume chung, text tin nhắn, các button Speak, Stop, Select all, Select none, và conversation agent (Assist).

## Services
Xem README.md.

## Blueprint
Import file `blueprints/automation/tts_broadcast/voice_announce.yaml` thủ công.

## Tạo pipeline Assist
Để phát thanh qua Assist, hãy tạo pipeline trợ giúp giọng nói sử dụng conversation agent TTS Broadcast:
1. Settings -> Voice assistants -> Add assistant.
2. Chọn conversation agent: `TTS Broadcast`.
3. Chọn engine STT (giọng nói thành văn bản) và TTS (văn bản thành giọng nói).
4. Lưu pipeline và ghi lại id của nó.
5. Trong card dashboard (hoặc ứng dụng di động), đặt `assist_pipeline_id` thành id pipeline đó (mặc định là `preferred`).

Hàng Assist trong YAML card được tạo ra dùng `pipeline_id: preferred` và tên đã bản địa hóa (`Assist` / `Trợ giúp`).

### Khắc phục "Nút micro không hiện"
- Pipeline cần một engine STT; nếu không có thì không có nút micro.
- Trang trình duyệt phải là HTTPS (hoặc dùng ứng dụng Companion Home Assistant) để truy cập micro.
- Hộp thoại chat riêng của conversation entity (mở từ trang entity) chỉ là văn bản theo thiết kế.

## Dashboard
Xem snippet trong README.md.

## Dashboard card
Card `tts-broadcast-card` tự phát hiện entity. Sau khi cài, hard refresh trình duyệt. Trong editor dashboard, Add card -> TTS Broadcast.

Lấy YAML fallback:
```yaml
service: tts_broadcast.get_dashboard_card
data:
  notify: true
```

## Phiên bản
v1.1.1: sửa được bước Voice phrases trong options flow, fallback clear/self-recursion, reply sai, static path, translations, và pipeline picker cho card.

## Giới hạn đã biết
- Dừng phát trên ESPHome qua `media_stop` chưa xác minh.
- Loa Tapo phụ thuộc thiết bị.
- Với LLM conversation agent, sentence trigger có thể cần bật "Prefer handling commands locally"; chưa xác minh.