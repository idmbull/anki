# 🎧 Anki Instant TTS (Click & Listen)

Add-on Anki giúp **phát âm tức thì** khi click vào từ vựng hoặc bôi đen câu văn. Sử dụng nguồn âm thanh trực tuyến chất lượng cao (Youdao, Oxford, Google) mà **không cần tải file MP3** về máy, giúp bộ thẻ nhẹ và đồng bộ nhanh hơn.

Đặc biệt tối ưu hóa cho **Tiếng Trung (Chinese)** với khả năng tách từ thông minh và **Tiếng Anh (English)** với giọng đọc Oxford chuẩn.

## ✨ Tính năng nổi bật

1.  **Click-to-Read (Click là đọc):**
    *   Click vào bất kỳ từ nào trong thẻ để nghe phát âm.
    *   **Thông minh:** Tự động phát hiện từ vựng.
2.  **Smart Segmentation cho Tiếng Trung:**
    *   Tự động tách từ trong câu liền mạch (Ví dụ: Câu `你们好`, khi click vào chữ `你`, add-on sẽ tự hiểu và đọc `你们` thay vì đọc từng chữ rời rạc).
    *   Sử dụng `Intl.Segmenter` native của trình duyệt, cực nhanh và chính xác.
3.  **Nguồn âm thanh đa dạng & chất lượng:**
    *   🇨🇳 **Tiếng Trung:** Ưu tiên **Youdao** (giọng tự nhiên, chuẩn bản xứ) -> Dự phòng Google.
    *   🇺🇸 **Tiếng Anh:** Ưu tiên **Oxford Learner's Dictionaries** (Giọng Mỹ chuẩn) -> Google.
    *   🌍 **Các ngôn ngữ khác:** Google Translate TTS (Hỗ trợ mọi ngôn ngữ: Nhật, Hàn, Pháp, Nga...).
4.  **Bluetooth Fix:**
    *   Tự động thêm khoảng lặng (silence) vào đầu đoạn audio để khắc phục lỗi bị mất âm đầu khi dùng tai nghe Bluetooth.
5.  **Selection Reader:**
    *   Bôi đen một đoạn văn bất kỳ và nhấn phím tắt (Mặc định: `F5`) để nghe cả câu.

## ⚙️ Cài đặt

1.  Mở Anki, chọn menu **Tools** -> **Add-ons**.
2.  Chọn nút **View Files**. Thư mục chứa add-on sẽ mở ra.
3.  Tạo một thư mục mới, đặt tên tùy ý (ví dụ: `Anki_Instant_TTS`).
4.  Copy file `__init__.py` (code bạn đang có) vào trong thư mục vừa tạo.
5.  Khởi động lại Anki.

## 📖 Hướng dẫn sử dụng

Để kích hoạt tính năng click-để-nghe, bạn cần thêm thuộc tính `tts="..."` vào trong **Card Template (Mẫu thẻ)**.

Vào **Tools** -> **Manage Note Types** -> Chọn loại thẻ -> **Cards**.

### 1. Dành cho Tiếng Trung (Khuyên dùng)
Sử dụng mã `zh` hoặc `cn`. Add-on sẽ kích hoạt chế độ tách từ thông minh và dùng nguồn Youdao.

```html
<div tts="zh">
    {{Hanzi}}
</div>
```
*Ví dụ câu: `我们去吃饭吧` -> Click vào `吃` sẽ đọc `吃饭`.*

### 2. Dành cho Tiếng Anh
Sử dụng mã `en`. Add-on sẽ ưu tiên tìm audio từ Oxford.

```html
<div tts="en">
    {{EnglishWord}}
</div>
<!-- Hoặc cả câu -->
<div tts="en">
    {{ExampleSentence}}
</div>
```

### 3. Dành cho Tiếng Nhật/Hàn/Khác
Sử dụng mã tương ứng (`ja`, `ko`, `fr`, `ru`...).

```html
<div tts="ja">
    {{Japanese}}
</div>
```

### 4. Đọc câu bất kỳ (Selection)
*   Bôi đen đoạn văn bản muốn nghe trên thẻ.
*   Nhấn phím **F5**.
*   *Lưu ý:* Nếu đoạn văn nằm trong thẻ `div` có `tts="zh"`, nó sẽ đọc giọng Trung. Nếu không xác định được, nó sẽ đọc ngôn ngữ mặc định (Tiếng Anh).

## 🔧 Cấu hình nâng cao

Bạn có thể mở file `__init__.py` bằng Notepad/VS Code để chỉnh sửa các thông số ở phần đầu file:

```python
# --- CẤU HÌNH ---
SHORTCUT_KEY = "F5"       # Phím tắt để đọc đoạn bôi đen
SILENCE_DURATION = 0.6    # Độ trễ (giây) để fix lỗi Bluetooth (tăng lên nếu vẫn bị mất âm)
DEFAULT_LANG = "en"       # Ngôn ngữ mặc định
```

## ⚠️ Lưu ý
*   Add-on yêu cầu kết nối Internet để tải âm thanh (lần đầu click).
*   Âm thanh được cache (lưu đệm) trong phiên làm việc, nhưng không lưu vĩnh viễn vào máy tính (để tiết kiệm dung lượng).