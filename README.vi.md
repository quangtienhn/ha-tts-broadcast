# TTS Broadcast

Custom integration cho Home Assistant để phát thông báo TTS đến nhiều loa.

## Cài qua HACS
1. HACS -> Integrations -> Custom repositories.
2. Thêm URL repo, chọn category Integration.
3. Cài "TTS Broadcast" và restart Home Assistant.
4. Thêm integration trong Settings -> Devices & Services.

## Cấu hình
Toàn bộ cấu hình qua UI.

## Entities
Một device "TTS Broadcast" với switch từng loa, volume chung, text tin nhắn, các button Speak, Stop, Select all, Select none.

## Services
Xem README.md.

## Blueprint
Import file `blueprints/automation/tts_broadcast/voice_announce.yaml` thủ công.

## Dashboard
Xem snippet trong README.md.

## Giới hạn đã biết
- Dừng phát trên ESPHome qua `media_stop` chưa xác minh.
- Loa Tapo phụ thuộc thiết bị.
- Với LLM conversation agent, sentence trigger có thể cần bật "Prefer handling commands locally"; chưa xác minh.