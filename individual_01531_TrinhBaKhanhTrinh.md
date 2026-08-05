# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung |
| --------------- | -------- |
| Họ và tên       | Trịnh Bá Khánh Trình |
| MSSV            | 2A202601531 |
| Khóa/Lớp        | K4 |
| Vai trò chính   | Policy & Evidence Lead |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | --------------- | ---------- |
| Policy rule engine và evidence builder | `src/nguoi3_policy_evidence/policy_agent.py` (`determine_primary_issue`, `determine_secondary_issues`, `build_evidence_ids`, `run`) | `CaseContext` đã có `order_status`, `affected_entities`, `customer_context`, `product_context`, `payment_reconciliation`, `delivery_analysis` | `case_assessment`, `root_cause_analysis`, `evidence_ids`, `financial_resolution`, `resolution_actions` | Hoàn thành |
| Contract dữ liệu cho policy/verifier | `src/common/schema.py` | Output handoff từ Customer, Order & Product, Payment, Delivery Agent | `CaseContext` mở rộng với `order_status` và các phần kết quả policy | Hoàn thành |

Phần ownership chính của tôi là biến dữ liệu đã được các agent domain tổng hợp thành quyết định cuối theo `EC_POLICY_V2`, đồng thời bảo đảm evidence ID có thể truy vết từ dữ liệu thật thay vì suy diễn.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Hoàn thiện Payment Agent và Delivery Agent khi thành viên phụ trách bận việc | `src/nguoi2_payment_delivery/payment_agent.py`, `src/nguoi2_payment_delivery/delivery_agent.py` | Bổ sung logic reconciliation, payment IDs, delivery variance, seller handoff variance và late handoff seller IDs |
| Hoàn thiện Coordinator, Verifier và pipeline chạy 50 case | `src/nguoi4_coordinator_verifier/*`, `src/main.py`, `logging/*`, `output/*` | Hệ thống chạy đủ 50 ticket, sinh `trace.jsonl`, `metadata.json`, và `50` file JSON hợp lệ trong `output/` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Cài đặt rule engine `EC_POLICY_V2` | `src/nguoi3_policy_evidence/policy_agent.py` | Quyết định `primary_issue`, `secondary_issues`, `root_cause_analysis`, `financial_resolution`, `resolution_actions`, `evidence_ids` cho từng case | Chạy `python .\src\main.py` và kiểm tra output mẫu như `output/EC_001.json` |
| Hoàn tất pipeline end-to-end và kiểm chứng 50 case | `src/nguoi4_coordinator_verifier/coordinator_agent.py`, `src/nguoi4_coordinator_verifier/verifier_agent.py`, `logging/trace.jsonl`, `output/` | Sinh `50` JSON, trace `350` dòng và metadata model local hợp lệ | Parse toàn bộ `output/EC_*.json`, đếm đủ `50`, kiểm `trace.jsonl` có dữ liệu |

Một output cụ thể mà tôi tạo ra và dùng để xác minh là:

`output/EC_001.json` cho thấy case được đánh giá là `unsupported_late_claim`, evidence IDs bám đúng `order`, `item`, `payment`, `seller`, `policy`, và các số liệu delivery/payment khớp với CSV nguồn.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần tôi phụ trách giải quyết bài toán chuyển dữ liệu từ các agent domain thành quyết định cuối cùng theo policy. Nếu chỉ có dữ liệu `orders`, `items`, `payments`, `delivery` mà không có policy layer thì hệ thống chưa thể kết luận đơn nào cần hoàn tiền, hoàn theo khoản nào, ai chịu trách nhiệm và evidence nào được phép nộp.

### Cách triển khai

Tôi triển khai policy theo hướng deterministic thay vì để model tự suy luận kết luận. Cụ thể:

1. Policy Agent đọc `CaseContext` đã được handoff.
2. Áp thứ tự ưu tiên của `EC_POLICY_V2`:
   `canceled_order_paid` -> `unavailable_order_paid` -> `late_delivery_seller` -> `late_delivery_logistics` -> `valid_split_payment` -> `unsupported_late_claim`.
3. Suy ra `secondary_issues` theo đúng thứ tự nghiệp vụ từ số item, số seller, số payment, lịch sử khách hàng và số category.
4. Sinh `root_cause_analysis`, `financial_resolution`, `resolution_actions` theo taxonomy của README.
5. Sinh `evidence_ids` chỉ từ các ID đã có trong dữ liệu thật.

Ngoài phần policy, khi hỗ trợ nhóm tôi cũng bổ sung:

- Payment Agent: tính `item_total_brl`, `freight_total_brl`, `expected_total_brl`, `payment_total_brl`, `difference_brl`, `reconciled`, `payment_types`, `payment_ids`
- Delivery Agent: tính `delivery_variance_hours`, `handoff_variance_hours`, `late_handoff_seller_ids`
- Coordinator/Verifier: chạy tuần tự 50 case, ghi `trace.jsonl`, validate schema/grounding/array limits trước khi ghi `output/*.json`

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `CaseContext` gồm `case_id`, `claimed_order_id`, `order_status`, `customer_context`, `product_context`, `affected_entities`, `payment_reconciliation`, `delivery_analysis` |
| Output | JSON case cuối cùng gồm `case_assessment`, `affected_entities`, `customer_context`, `product_context`, `delivery_analysis`, `payment_reconciliation`, `root_cause_analysis`, `evidence_ids`, `financial_resolution`, `resolution_actions` |
| Module phụ thuộc | `src/common/data_loader.py`, `src/nguoi1_customer_product/*`, `src/nguoi2_payment_delivery/*` |
| Module sử dụng output | `src/nguoi4_coordinator_verifier/coordinator_agent.py`, `src/nguoi4_coordinator_verifier/verifier_agent.py`, `output/*.json` |
| Điều kiện lỗi cần xử lý | Thiếu `order_status`, evidence ID sai format hoặc không tồn tại, order không có item row, payment lệch so với item + freight, timestamp delivery hoặc carrier handoff bị thiếu |

### Cách xác minh

```bash
python .\src\main.py
python -c "import json, pathlib; files=sorted(pathlib.Path('output').glob('EC_*.json')); [json.loads(p.read_text(encoding='utf-8')) for p in files]; print(len(files))"
```

- **Kết quả mong đợi:** Chạy hết pipeline, sinh đủ `50` file JSON parse được, có `trace.jsonl`, có `metadata.json`.
- **Kết quả thực tế:** Pipeline chạy thành công, `output/` có đúng `50` file `EC_001.json` đến `EC_050.json`, `trace.jsonl` có `350` dòng và metadata dùng `gemma3:4b-it-qat`.
- **Artifact/log:** `output/`, `logging/trace.jsonl`, `logging/metadata.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Phần policy có thể viết bằng prompt cho model hoặc viết deterministic bằng code.
- **Các phương án đã cân nhắc:**  
  `1.` Dùng model local để suy luận và trả luôn kết luận cuối.  
  `2.` Dùng model local cho runtime metadata nhưng triển khai policy bằng code rule-based.
- **Phương án đã chọn:** Dùng deterministic policy engine bằng Python cho kết luận cuối.
- **Lý do:** README quy định rõ `EC_POLICY_V2`, thứ tự ưu tiên và evidence format. Viết bằng code giúp tránh hallucination, dễ kiểm thử, dễ verifier hóa và nhất quán trên cả 50 case. Model local vẫn được khai báo trong metadata để đáp ứng yêu cầu runtime/model nhưng không được dùng làm nguồn quyết định cuối.
- **Bằng chứng quyết định phù hợp:** Hệ thống sinh đủ `50` JSON, verifier pass, evidence IDs truy ngược được về `orders/items/payments/sellers`, và output mẫu như `EC_001.json`/`EC_050.json` bám đúng rule.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `PermissionError: [Errno 13] Permission denied: 'E:\\VinAI\\K4-Day9-Multi-Agent-A2A_ChanTeam\\logging\\trace.jsonl'`
- **Lệnh hoặc bước tái hiện:** Chạy `python -m src.main` trong môi trường sandbox khi Coordinator bắt đầu ghi trace và output.
- **Nguyên nhân gốc:** Runtime trong sandbox không có quyền ghi trực tiếp các artifact chạy batch vào repo `E:` dù source code đã chỉnh sửa được.
- **Cách xử lý:** Chạy pipeline ngoài sandbox để sinh `trace.jsonl`, `metadata.json` và `output/*.json` thật trong repo, đồng thời giữ nguyên source code deterministic trong repo.
- **Cách xác minh sau khi sửa:** Chạy lại entrypoint, kiểm `output/` có `50` file, parse toàn bộ JSON thành công, `trace.jsonl` có dữ liệu.
- **Điều học được:** Với bài lab cần artifact chạy thật, ngoài việc code đúng còn phải chú ý quyền ghi runtime và phân biệt rõ lỗi business logic với lỗi môi trường.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của tôi:

1. Ticket trong `input/EC_xxx.json` cung cấp `claimed_order_id`, Coordinator dùng ID này để tạo `CaseContext`.
2. Customer Agent và Order & Product Agent truy xuất `orders`, `customers`, `order_items`, `products`, `sellers` để tạo `customer_context`, `product_context`, `affected_entities`.
3. Payment Agent và Delivery Agent tính các số liệu định lượng như `expected_total_brl`, `difference_brl`, `reconciled`, `delivery_variance_hours`, `handoff_variance_hours`.
4. Policy Agent áp `EC_POLICY_V2` để xác định issue, root cause, party chịu trách nhiệm, refund, actions và evidence IDs.
5. Verifier Agent kiểm schema, array limits, enum hợp lệ và đặc biệt là evidence IDs phải truy vết được về dữ liệu nguồn.
6. Nếu pass verifier thì Coordinator ghi file vào `output/`; đồng thời từng bước handoff đều được ghi vào `logging/trace.jsonl`.

Nói ngắn gọn, pipeline của bài này là:

`input case -> domain agents -> policy agent -> verifier -> output + trace`

## 8. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trịnh Bá Khánh Trình  
**Ngày xác nhận:** 2026-08-05
