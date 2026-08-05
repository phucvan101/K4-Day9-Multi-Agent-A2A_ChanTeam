# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                            |
| --------------- | ------------------------------------ |
| Họ và tên       | Nguyễn Văn Phúc                      |
| MSSV            | 01350                                |
| Khóa/Lớp        | K4                                   |
| Vai trò chính   | Người 1 — Customer & Product Data Lead |
| Ngày hoàn thành | 2026-08-05                           |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data loader dùng chung (đọc/join CSV) | `src/common/data_loader.py` — `load_order`, `load_items`, `load_payments`, `load_sellers`, `load_products`, `load_customer_history` | `order_id` / `customer_unique_id` / danh sách `seller_id`, `product_id` | `dict`/`list[dict]` đã join từ `orders`, `customers`, `order_items`, `sellers`, `products` | Một phần — logic đã chạy đúng, chưa loop qua đủ 50 case trong `input/` |
| Customer Agent | `src/nguoi1_customer_product/customer_agent.py` — `run()` | `claimed_order_id` | `CustomerContext(customer_unique_id, related_order_ids)` | Một phần — đã test 1 case thật + case `order_id` không tồn tại |
| Order & Product Agent | `src/nguoi1_customer_product/order_product_agent.py` — `run()` | `claimed_order_id` | `AffectedEntities(order_ids, item_ids, seller_ids)`, `ProductContext(product_ids, category_names)` | Một phần — đã test case có item + case order không có item nào |

Chỉ nhận ownership 3 module trên. Payment Agent, Delivery Agent (Người 2), Policy Agent (Người 3), Coordinator/Verifier Agent (Người 4) không thuộc phạm vi tôi trực tiếp code.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Cài đặt và test hạ tầng model local (Ollama + qwen2.5:7b-instruct) | Người 3 (Policy Agent), Người 4 (`metadata.json`) | Xác nhận model gọi được qua API local (`http://localhost:11434`), nhưng phát hiện model trả **sai** khi dùng để classify `primary_issue` trực tiếp (trả `valid_split_payment` cho case không liên quan gì đến payment) → kết luận và ghi vào `architecture.md` mục 6: Policy Agent phải là rule engine deterministic, không dùng LLM để ra quyết định |
| Soạn `architecture.md` (sơ đồ agent, bảng quyền truy cập, luồng handoff, quyết định model) | Cả nhóm | File `architecture.md` ở root repo, có sơ đồ Mermaid + bảng ánh xạ 4 người |
| Tạo cấu trúc thư mục code khởi tạo cho cả 4 người | Người 2, 3, 4 | `src/common/`, `src/nguoi1_.../`, `src/nguoi2_.../`, `src/nguoi3_.../`, `src/nguoi4_.../` với skeleton function + docstring contract |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Đọc/join `orders.csv` + `customers.csv` theo `order_id`, cache DataFrame bằng `lru_cache` | `src/common/data_loader.py::load_order` | `dict` gồm toàn bộ cột `orders` + `customer_unique_id` đã join | Chạy `load_order('9b75cdaf2d85857ef023980e15d01546')` → trả đúng `order_status=delivered`, có `customer_unique_id` |
| Xác định lịch sử mua hàng cùng khách (loại trừ order hiện tại) | `src/common/data_loader.py::load_customer_history` | `list[order_id]` các order khác cùng `customer_unique_id` | Chạy với case trên → trả `['65bbd0719855fe808bb19f62dfa9f42c']`, không chứa order hiện tại |
| Ráp `CustomerContext` cho Customer Agent | `src/nguoi1_customer_product/customer_agent.py::run` | `CustomerContext(customer_unique_id, related_order_ids[:5])` | Test case thật + test `order_id='does-not-exist'` → trả context rỗng, không crash |
| Ráp `AffectedEntities` + `ProductContext` cho Order & Product Agent, sinh `item_ids` đúng định dạng `<order_id>:<order_item_id>` | `src/nguoi1_customer_product/order_product_agent.py::run` | `AffectedEntities(order_ids, item_ids[:5], seller_ids[:3])`, `ProductContext(product_ids[:5], category_names[:5])` | Test case EC_001 (2 item, 1 seller, 1 category) + test order không có item nào (`8e24261a7e58791d10cb1bf9da94df5c`) → trả đúng mảng rỗng theo README mục 4 |

Một output cụ thể phần việc của tôi tạo ra:

Với `claimed_order_id = 9b75cdaf2d85857ef023980e15d01546` (case `EC_001`), `order_product_agent.run()` trả về:
`AffectedEntities(order_ids=['9b75...'], item_ids=['9b75...:1', '9b75...:2'], seller_ids=['c70c1b0d...'], payment_ids=[])` và `ProductContext(product_ids=[2 id], category_names=['beleza_saude'])` — đúng format evidence ID README mục 5 yêu cầu (`item:<order_id>:<order_item_id>`), sẵn sàng cho Policy Agent dùng để sinh `evidence_ids`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần của tôi giải quyết bước đầu tiên của pipeline: từ `claimed_order_id` duy nhất trong input, truy xuất và join đúng các bảng CSV liên quan đến khách hàng, item, seller, sản phẩm — để các agent phía sau (Payment, Delivery, Policy) có dữ liệu sạch, không phải tự đọc CSV lại từ đầu.

### Cách triển khai

`data_loader.py` đọc mỗi CSV đúng 1 lần, cache bằng `functools.lru_cache(maxsize=1)` ở cấp module — vì hệ thống phải chạy qua 50 case, đọc lại `pandas.read_csv` mỗi lần gọi hàm sẽ rất chậm. Các hàm `load_*` chỉ filter trên DataFrame đã cache trong RAM bằng `.loc[...]` hoặc `.isin(...)`, trả về `dict`/`list[dict]` thay vì `DataFrame` để các agent khác không cần biết pandas.

`customer_agent.run()` gọi `load_order` lấy `customer_unique_id`, sau đó gọi `load_customer_history` với tham số `exclude_order_id` để đảm bảo order hiện tại không tự xuất hiện trong `related_order_ids` của chính nó.

`order_product_agent.run()` gọi `load_items`, dùng `dict.fromkeys(...)` để khử trùng lặp `seller_id`/`product_id` mà vẫn giữ thứ tự xuất hiện đầu tiên (giữ ổn định theo dữ liệu nguồn — README mục 6 yêu cầu array giữ thứ tự ổn định), rồi cắt theo đúng giới hạn mảng của schema (`item_ids<=5`, `seller_ids<=3`, `product_ids<=5`, `category_names<=5`).

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `claimed_order_id: str` từ `input/EC_xxx.json` (do Coordinator truyền vào) |
| Output | `CustomerContext`, `AffectedEntities`, `ProductContext` (dataclass định nghĩa ở `src/common/schema.py`) |
| Module phụ thuộc | `src/common/data_loader.py`, `src/common/schema.py`, các CSV trong `data/` |
| Module sử dụng output | `src/nguoi3_policy_evidence/policy_agent.py` (Người 3), qua Coordinator (Người 4) |
| Điều kiện lỗi cần xử lý | `order_id` không tồn tại trong `orders.csv` → trả context rỗng thay vì raise; order không có item row nào → `item_ids`/`seller_ids`/`product_ids`/`category_names` phải là mảng rỗng (README mục 4), không phải `null` |

### Cách xác minh

```bash
python3 -c "
from src.nguoi1_customer_product.customer_agent import run as customer_run
from src.nguoi1_customer_product.order_product_agent import run as order_product_run
order_id = '9b75cdaf2d85857ef023980e15d01546'
print(customer_run(order_id))
print(order_product_run(order_id))
"
```

- **Kết quả mong đợi:** `CustomerContext` có `customer_unique_id` khác `None` và `related_order_ids` không chứa order hiện tại; `AffectedEntities`/`ProductContext` phản ánh đúng số item/seller/category thật của order.
- **Kết quả thực tế:** Đúng như mong đợi — `related_order_ids=['65bbd0719855fe808bb19f62dfa9f42c']`, 2 item cùng 1 seller, 1 category `beleza_saude`.
- **Artifact/log:** Chạy trực tiếp qua REPL trong phiên làm việc, chưa lưu thành file log/test tự động — cần bổ sung `pytest` hoặc script batch-test trước khi nộp.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần quyết định cách đọc CSV cho các hàm `load_*` — hệ thống phải chạy 50 case, mỗi case gọi nhiều hàm data_loader khác nhau.
- **Các phương án đã cân nhắc:** (1) Gọi `pd.read_csv()` mới mỗi lần hàm được gọi — đơn giản, nhưng đọc lại file hàng chục MB nhiều lần; (2) Cache DataFrame ở module-level bằng `functools.lru_cache(maxsize=1)`, đọc CSV đúng 1 lần cho cả tiến trình.
- **Phương án đã chọn:** Phương án 2 — cache bằng `lru_cache`.
- **Lý do:** Với 50 case × nhiều lần gọi `load_order`/`load_items`/..., đọc lại CSV mỗi lần sẽ cộng dồn I/O không cần thiết; cache một lần đánh đổi bằng việc giữ toàn bộ DataFrame trong RAM (chấp nhận được vì `data/` chỉ ~120MB).
- **Bằng chứng quyết định phù hợp:** Sau khi cache, các lệnh test lặp lại (`load_order`, `load_items`, `load_sellers`, `load_products`, `load_customer_history` gọi liên tiếp trong cùng 1 process) trả kết quả tức thì, không có độ trễ đọc file lặp lại.

## 6. Một lỗi hoặc blocker đã xử lý

Trong phạm vi việc đã test, tôi không gặp lỗi runtime nào cần fix ngược lại. Rủi ro lớn nhất tôi chủ động phòng trước (không phải bug được phát hiện sau khi chạy lỗi) là 2 edge case README mục 4 cảnh báo rõ:

- **Rủi ro 1:** Order không có item row nào (có thật trong `data/olist_order_items_dataset.csv` — không phải mọi order đều có item, ví dụ order_status `unavailable`/`canceled` sớm). Nếu không xử lý, `order_product_agent.run()` có thể trả về mảng `None` hoặc raise lỗi thay vì mảng rỗng.
  - **Cách xử lý:** `load_items()` dùng `.loc[...]` trên DataFrame rỗng vẫn trả `DataFrame` rỗng hợp lệ, `.to_dict("records")` trả `[]` tự nhiên — không cần try/except.
  - **Cách xác minh:** Test với `order_id='8e24261a7e58791d10cb1bf9da94df5c'` (order thật không có item) → `AffectedEntities(item_ids=[], seller_ids=[])`, `ProductContext(product_ids=[], category_names=[])`, đúng README mục 4.
- **Rủi ro 2:** `claimed_order_id` trong input không khớp `order_id` nào trong CSV.
  - **Cách xử lý:** `load_order()` trả `None` thay vì raise `IndexError` khi `.iloc[0]` trên kết quả rỗng; `customer_agent.run()` kiểm tra `if order is None` trước khi dùng.
  - **Cách xác minh:** Test với `order_id='does-not-exist'` → trả `CustomerContext()` rỗng, không crash chương trình.

**Điều học được:** Với dữ liệu thật (không phải dữ liệu mock), luôn phải tự tìm ví dụ biên thật trong CSV (dùng `set` difference giữa `orders.order_id` và `order_items.order_id`) để test, thay vì chỉ tin vào 1 case "đẹp" như `EC_001`.

Phạm vi chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** Toàn bộ 3 module trên mới test thủ công 2-3 case, chưa chạy vòng lặp qua đủ 50 file trong `input/`.
- **Những gì đã loại trừ:** Đã xác nhận không lỗi với case có item/không có item/order không tồn tại — chưa xác nhận case nhiều seller (`multi_seller_order`) hay nhiều category (`multiple_categories`) trên dữ liệu thật.
- **Bước tiếp theo:** Viết script loop qua `input/EC_001.json` → `EC_050.json`, gọi cả 2 agent, log lỗi nếu có exception hoặc field `None` bất thường trước khi bàn giao cho Người 3/Người 4 tích hợp.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ 9 file CSV (`data/`) → Coordinator đọc `claimed_order_id` từ `input/EC_xxx.json` → 4 agent thu thập (Customer, Order&Product, Payment, Delivery) join CSV song song, trả về context riêng từng domain → Policy Agent tổng hợp tất cả context, áp `EC_POLICY_V2` theo đúng thứ tự ưu tiên để ra `primary_issue`, `root_cause`, `refund`, `evidence_ids` → Verifier Agent kiểm evidence có thật trong CSV, kiểm array limit/null handling → ghi `output/EC_xxx.json`.
2. Evidence ID (`order:`, `item:`, `payment:`, `seller:`, `policy:`) chính là "ground truth" của bài này — không có tập evaluation riêng, mà evidence phải tự dựng được từ dòng CSV thật; Verifier Agent đóng vai trò kiểm chứng evidence đó có tồn tại thật, không phải agent tự bịa ra.
3. Ngoài Verifier, còn 2 lớp quality check khác: (a) giới hạn mảng cứng trong output schema (tối đa 5 order/item/product/category, 3 seller...) buộc từng agent phải tự cắt bớt đúng chỗ chứ không đẩy hết sang Verifier; (b) `null` handling bắt buộc khi order không có item (`expected_total_brl`, `difference_brl`, `reconciled` phải là `null`, không phải `0` hay bỏ field).
4. Phải áp đúng thứ tự ưu tiên bảng policy vì nhiều case có thể thỏa nhiều điều kiện cùng lúc (vừa `canceled` vừa giao trễ) — nếu không cố định thứ tự, 2 lần chạy cùng 1 case có thể ra `primary_issue` khác nhau, phá vỡ tính xác định (deterministic) mà cả bài yêu cầu.
5. Một agent được coi là "hoàn thành đúng" khi: (a) output khớp `CaseContext`/schema mà agent kế tiếp cần, (b) test qua ít nhất 1 case có dữ liệu và 1 case biên (order không có item / `order_id` không hợp lệ) không crash, và (c) Verifier Agent duyệt được record cuối cùng ghi ra `output/` mà không reject.

## 8. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Phúc
**Ngày xác nhận:** 2026-08-05
