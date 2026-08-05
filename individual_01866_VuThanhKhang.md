# Member Role Report — Day 9: Multi Agent A2A

> Báo cáo cá nhân hoàn thành bởi thành viên. Thay nội dung trong dấu `[ ]` khi cần.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                           |
| --------------- | ---------------------------------- |
| Họ và tên       | Vũ Thanh Khang                     |
| MSSV            | 01866                              |
| Khóa/Lớp        | K4                                 |
| Vai trò chính   | Người 2 — Payment & Delivery Agent |
| Ngày hoàn thành | 2026-08-05                         |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                    | File/hàm phụ trách                              | Input nhận vào                | Output bàn giao                                                                                                                                         | Trạng thái |
| ------------------------------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Payment reconciliation + evidence ids | `src/nguoi2_payment_delivery/payment_agent.py`  | `claimed_order_id` (order_id) | `PaymentReconciliation` (item_total_brl, freight_total_brl, expected_total_brl, payment_total_brl, difference_brl, reconciled), `payment_ids`           | Hoàn thành |
| Delivery analysis and seller handoff  | `src/nguoi2_payment_delivery/delivery_agent.py` | `claimed_order_id` (order_id) | `DeliveryAnalysis` (delivered_at, estimated_delivery_at, carrier_handoff_at, delivery_variance_hours, seller_handoff_analysis, late_handoff_seller_ids) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                | Thành viên/module được hỗ trợ                          | Kết quả                                                              |
| ------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------- |
| Tích hợp với Coordinator | `src/nguoi4_coordinator_verifier/coordinator_agent.py` | Hoàn thành: cung cấp evidence và kết quả phân tích cho bước tổng hợp |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                | File/hàm/artifact liên quan                     | Kết quả bàn giao               | Cách xác minh                                                                                      |
| ------------------------------------ | ----------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------- |
| Payment reconciliation computation   | `src/nguoi2_payment_delivery/payment_agent.py`  | `PaymentReconciliation` object | `python -c "from src.nguoi2_payment_delivery.payment_agent import run; print(run('<order_id>'))"`  |
| Delivery variance & handoff analysis | `src/nguoi2_payment_delivery/delivery_agent.py` | `DeliveryAnalysis` object      | `python -c "from src.nguoi2_payment_delivery.delivery_agent import run; print(run('<order_id>'))"` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

[Phần của bạn giải quyết vấn đề gì trong pipeline?]

Người 2 chịu trách nhiệm phân tích hai domain chính cho mỗi `claimed_order_id`:

- Payment reconciliation: đối soát tổng payment với tổng item + freight, xác định `difference_brl` và cờ `reconciled`.
- Delivery and seller handoff: tính `delivery_variance_hours`, kiểm tra thời điểm carrier nhận hàng so với `shipping_limit_date` của seller để phát hiện seller bàn giao muộn.

### Cách triển khai

[Mô tả thuật toán, quy tắc dữ liệu, orchestration hoặc quyết định chính.]

Triển khai chính:

- `payment_agent.run(claimed_order_id)` đọc `order_items` và `order_payments` qua `src.common.data_loader`, tổng item giá và freight, làm tròn 2 chữ số, so sánh với tổng payment; đánh dấu `reconciled` nếu sai số <= 0.10 BRL.
- `delivery_agent.run(claimed_order_id)` đọc `orders` và `order_items`, tính `delivery_variance_hours = order_delivered_customer_date - order_estimated_delivery_date`, xác định `earliest_shipping_limit_date` cho mỗi seller trong order và tính `handoff_variance_hours = order_delivered_carrier_date - shipping_limit_date`. Nếu `handoff_variance_hours > 0` thì seller bị `late_handoff`.

Các quyết định nhỏ:

- Lấy `earliest_shipping_limit_date` theo seller để tránh đánh giá nhầm khi seller có nhiều item với shipping_limit khác nhau.
- Giới hạn trả lại tối đa 3 seller trong `late_handoff_seller_ids` để kết quả ngắn gọn cho báo cáo.

### Input, output và contract

| Thành phần              | Mô tả                                                           |
| ----------------------- | --------------------------------------------------------------- |
| Input                   | `claimed_order_id` (str)                                        |
| Output                  | `PaymentReconciliation`, `DeliveryAnalysis`                     |
| Module phụ thuộc        | `src/common/data_loader.py`, CSV files trong `data/`            |
| Module sử dụng output   | `src/nguoi4_coordinator_verifier/coordinator_agent.py`          |
| Điều kiện lỗi cần xử lý | Mất row item/payments; order không tồn tại; timestamp thiếu/NaN |

### Cách xác minh

```bash
# Chạy kiểm tra nhanh cho một order (thay <order_id> bằng order có trong data/)
python - <<'PY'
from src.nguoi2_payment_delivery.payment_agent import run as payment_run
from src.nguoi2_payment_delivery.delivery_agent import run as delivery_run
print(payment_run('<order_id>'))
print(delivery_run('<order_id>'))
PY

# Hoặc chạy toàn bộ pipeline (Coordinator)
python src/main.py
```

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần xác định seller handoff muộn khi có nhiều item/seller với shipping_limit khác nhau.
- **Các phương án đã cân nhắc:**
    - Dùng shipping_limit của từng item trực tiếp (item-level assessment).
    - Tính `earliest_shipping_limit_date` theo seller rồi so sánh (đã chọn).
- **Phương án đã chọn:** Tính `earliest_shipping_limit_date` theo seller.
- **Lý do:** Đảm bảo đánh giá seller có trách nhiệm giao hàng sớm nhất; tránh false-negative khi một seller có một item muộn nhưng có item khác với shipping_limit sớm hơn.
- **Bằng chứng quyết định phù hợp:** So sánh manual với sample orders cho thấy phương án chọn bắt được seller vi phạm chính xác hơn.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Model trả về `None` cho `order_delivered_carrier_date` gây lỗi khi so sánh timestamp.
- **Lệnh hoặc bước tái hiện:** Chạy `delivery_agent.run(order_without_carrier_date)` trên order thiếu trường `order_delivered_carrier_date`.
- **Nguyên nhân gốc:** Một số row `orders` có giá trị NaN/None cho trường này.
- **Cách xử lý:** Thêm hàm `_parse_timestamp` kiểm tra `None`/NaN và trả `None` an toàn; `_variance_hours` trả `None` nếu timestamp thiếu.
- **Cách xác minh sau khi sửa:** Chạy `delivery_agent.run` trên same order, kết quả trả `DeliveryAnalysis` với `carrier_handoff_at=None` và không raise exception.
- **Điều học được:** Luôn kiểm tra missing/NaN trong dữ liệu thô trước khi tính toán thời gian.

## 7. Hiểu biết về luồng end-to-end

[Viết ngắn các câu trả lời cho các câu hỏi luồng end-to-end ở đây.]

1. Dữ liệu đi từ CSV `data/` tới các agent qua `src/common/data_loader.py`, các agent xử lý và trả về dataclass (`PaymentReconciliation`, `DeliveryAnalysis`) cho `coordinator_agent`.
2. Evaluation set: dùng `input/` (50 case) làm tập đầu vào; ground-truth document IDs không có sẵn trong lab này — so sánh chủ yếu bằng kiểm tra logic và sanity checks.
3. Quality checks: đơn vị kiểm tra `reconciled` và `delivery_variance_hours` là các phép kiểm tra chính; freshness monitoring không áp dụng với dataset tĩnh.
4. Vì sao dùng cùng test set: để đảm bảo các agent so sánh cùng bộ case, reproduciability và để so sánh kết quả giữa các phiên.
5. Repair thành công khi output phù hợp với policy `EC_POLICY_V2` và khi các action (refund/explain/reject) có thể được đưa ra deterministically từ dữ liệu.

## 8. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Vũ Thanh Khang
**Ngày xác nhận:** 2026-08-05
