# Bao cao ca nhan - Day 9: Multi-Agent A2A

## 1. Thong tin ca nhan

| Thong tin | Noi dung |
| --- | --- |
| Ho va ten | Nguyễn Hữu Tuyến |
| 5 so cuoi MSV | 01520 |
| Khoa/Lop | K4 |
| Vai tro chinh | Coordinator & Verifier / Infra Lead |
| Ngay hoan thanh | 2026-08-05 |

## 2. Vai tro va pham vi cong viec

Trong kien truc nhom, toi phu trach nhom 4 gom `Coordinator Agent`, `Verifier Agent` va cac phan ha tang lien quan den trace, metadata, dong goi output. Pham vi nay nam o buoc cuoi cua pipeline: nhan ket qua tu cac agent domain, tong hop case context, kiem tra tinh hop le theo schema va ghi ket qua cuoi cung vao thu muc `output/`.

| Module/deliverable | File/hang muc phu trach | Input nhan vao | Output ban giao | Trang thai |
| --- | --- | --- | --- | --- |
| Coordinator Agent | `src/nguoi4_coordinator_verifier/coordinator_agent.py` | `input/EC_xxx.json`, ket qua Customer/Product/Payment/Delivery/Policy | Case context day du, san sang verify | Hoan thanh |
| Verifier Agent | `src/nguoi4_coordinator_verifier/verifier_agent.py` | Case context tu Policy Agent | JSON hop le theo output schema hoac loi reject | Hoan thanh |
| Evidence index | `src/nguoi4_coordinator_verifier/evidence_index.py` | CSV trong `data/` | Tap evidence ID co that de doi chieu | Hoan thanh |
| Trace va metadata | `trace.jsonl`, `metadata.json` | Su kien chay pipeline, thong tin model/runtime | Log chay that va mo ta model <= 10B | Hoan thanh |
| Output package | `output/`, `output.zip` | 50 case da verify | 50 file JSON nop bai | Hoan thanh |

Ngoai pham vi chinh, toi ho tro tich hop cac agent nguoi 1, 2, 3 vao mot luong xu ly thong nhat, bao dam output cua tung agent duoc dua vao dung truong trong schema cuoi cung.

## 3. Ket qua theo vai tro

| Nhiem vu da thuc hien | Artifact lien quan | Ket qua ban giao | Cach xac minh |
| --- | --- | --- | --- |
| Dieu phoi luong A2A cho moi case | `coordinator_agent.py` | Pipeline doc input, goi cac agent domain, tong hop ket qua | Chay `python -m src.main` |
| Kiem tra schema va gioi han array | `verifier_agent.py` | Output dung cac truong bat buoc, `confidence` trong `[0,1]`, gioi han evidence/actions/entities | Chay `pytest tests/test_verifier.py` |
| Kiem tra evidence ID co that | `evidence_index.py` | Chi chap nhan `order:`, `item:`, `payment:`, `seller:`, `policy:` hop le | Doi chieu voi CSV trong `data/` |
| Ghi trace chay that | `trace.py`, `trace.jsonl` | Luu cac buoc coordinator, policy, verifier cho 50 case | Kiem tra `trace.jsonl` sau khi chay |
| Dong goi ket qua | `output.zip` | Zip chua dung 50 JSON `EC_001.json` den `EC_050.json` | Kiem tra so luong file trong `output/` |

Ket qua cuoi cung cua phan viec la pipeline co the xu ly 50 input dispute case, sinh output theo schema README muc 6 va co trace/metadata de giai trinh qua trinh chay.

## 4. Giai thich ky thuat da thuc hien

### Van de can giai quyet

Bai toan khong chi can tao nhieu agent theo ten, ma can co luong handoff ro rang giua cac domain du lieu. Phan toi phu trach giai quyet viec dieu phoi dau vao/dau ra cua cac agent, tranh mat context khi chuyen buoc, va chan cac output khong hop le truoc khi ghi file nop bai.

### Cach trien khai

`Coordinator Agent` nhan `case_id`, `claimed_order_id` va `policy_version` tu input. Sau do coordinator khoi tao case context va phan phoi order id cho cac agent domain:

- Customer Agent tra ve `customer_unique_id`, `related_order_ids`, co lap lai khach hang.
- Order & Product Agent tra ve item, seller, product, category va cac co multi-item/multi-seller/multiple-categories.
- Payment Agent doi soat tong payment voi tong item + freight.
- Delivery Agent tinh delivery variance va seller handoff variance.
- Policy Agent ap dung `EC_POLICY_V2` de xac dinh issue, responsible party, refund, action va evidence.

Sau khi co case assessment, `Verifier Agent` thuc hien cac lop kiem tra: schema, null handling, gioi han mang, thu tu secondary issues/actions, evidence ID, dinh dang timestamp va tinh hop le cua cac truong tien te. Neu hop le thi coordinator ghi file vao `output/`; neu khong hop le thi reject va ghi ly do vao trace.

### Input, output va contract

| Thanh phan | Mo ta |
| --- | --- |
| Input | `input/EC_xxx.json` gom `case_id`, `customer_request.claimed_order_id`, `policy_version` |
| Output | `output/EC_xxx.json` theo schema README muc 6 |
| Module phu thuoc | `src/common/data_loader.py`, cac agent nguoi 1, 2, 3 |
| Module su dung output | Verifier, trace logger, output writer |
| Dieu kien loi can xu ly | Evidence ID khong ton tai, sai gioi han array, sai null handling, sai thu tu action/secondary issue |

### Cach xac minh

```bash
python -m src.main
pytest tests/test_coordinator.py tests/test_verifier.py
```

- Ket qua mong doi: tao du 50 file JSON trong `output/`, trace moi trong `trace.jsonl`, khong co case vi pham schema/evidence.
- Artifact/log: `output/`, `output.zip`, `trace.jsonl`, `metadata.json`.

## 5. Mot quyet dinh ky thuat quan trong

- Boi canh: Policy Agent can evidence ID de giai thich ket luan, nhung README yeu cau khong duoc tao bang chung khong ton tai trong CSV.
- Cac phuong an da can nhac: de Policy Agent tu sinh evidence theo prompt; hoac tao index evidence tu CSV roi de Verifier kiem tra bat buoc.
- Phuong an da chon: dung `EvidenceIndex` va `Verifier Agent` lam cong kiem soat cuoi.
- Ly do: cach nay tang do dung va kha nang tai lap, tranh false positive evidence, dong thoi phu hop rang buoc "chi dung evidence ID co the dung truc tiep tu du lieu".
- Bang chung: evidence trong output chi nam trong cac dang `order:<id>`, `item:<order_id>:<item_id>`, `payment:<order_id>:<payment_sequential>`, `seller:<seller_id>`, `policy:<root_cause_code>`.

## 6. Mot loi hoac blocker da xu ly

- Trieu chung: output co nguy co sai khi order khong co item row hoac payment/item khong doi soat duoc, dan den `expected_total_brl`, `difference_brl`, `reconciled` bi dien gia tri suy doan.
- Buoc tai hien: chay pipeline voi cac case co order trang thai `canceled`/`unavailable` va thieu item row.
- Nguyen nhan goc: neu khong tach logic verifier, cac agent phia truoc de dien gia tri mac dinh thay vi `null`.
- Cach xu ly: bo sung rule trong verifier/null contract: khi khong co item row thi cac truong doi soat phu thuoc item phai la `null`, cac mang item/seller/product/category de rong.
- Cach xac minh sau khi sua: chay test verifier va kiem tra output JSON tuong ung khong con evidence/item khong ton tai.
- Dieu hoc duoc: voi bai multi-agent, guardrail o buoc cuoi quan trong ngang voi logic suy luan cua agent domain.

## 7. Hieu biet ve luong end-to-end

He thong bat dau tu 50 file `input/EC_001.json` den `EC_050.json`. Moi file chua order ma khach hang khieu nai. Coordinator doc input va dung `claimed_order_id` de dieu phoi cac agent theo domain.

Customer Agent va Order & Product Agent lay du lieu tu `customers.csv`, `orders.csv`, `order_items.csv`, `products.csv`, `sellers.csv` de xac dinh khach hang, lich su order, item, seller va category. Payment Agent dung `order_payments.csv` va `order_items.csv` de tinh `expected_total_brl`, `payment_total_brl`, `difference_brl`. Delivery Agent dung timestamp trong `orders.csv` va `shipping_limit_date` de tinh giao hang tre va seller ban giao tre.

Policy Agent ap dung `EC_POLICY_V2` theo thu tu uu tien: canceled/unavailable paid, late delivery do seller/logistics, valid split payment, unsupported late claim. Ket qua policy gom primary issue, secondary issues, root cause, responsible parties, refund, actions va evidence IDs.

Verifier Agent la buoc kiem soat cuoi: doi chieu evidence voi CSV, kiem tra schema, gioi han array, thu tu business rule, null handling va gia tri tien/gio da lam tron 2 chu so. Chi case hop le moi duoc ghi vao `output/EC_xxx.json`. Toan bo qua trinh duoc ghi vao `trace.jsonl`, thong tin model/runtime nam trong `metadata.json`, va san pham nop bai la `output.zip`.

## 8. Cam ket cua thanh vien

- [x] Noi dung bao cao phan anh dung phan viec va muc hieu cua toi.
- [x] Toi co the giai thich luong end-to-end, khong chi module minh phu trach.
- [x] Toi khong ghi "da chay thanh cong" cho phan chua duoc kiem chung.
- [x] Bao cao khong chua `.env`, API key, token hoac secret.
- [x] Bao cao nay khong phai ban sao nguyen van cua bao cao nhom hoac bao cao thanh vien khac.

**Ho va ten:** Nguyễn Hữu Tuyến  
**Ngay xac nhan:** 2026-08-05
