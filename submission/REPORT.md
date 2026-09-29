# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Vũ Quang Tiến
- **MSSV:** 2A202602872
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/vuquangtien/K4-L3A-Day13-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602872`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.html` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 (CP1) | Đã có correlation ID, request context và PII redaction; xem `evidence/02-log-validator.txt`. |
| `validate_dashboard.py` | 6/6 panel hợp lệ | 6/6 panel hợp lệ (CP2) | Dashboard runtime gồm 6 panel được render từ `data/logs.jsonl`; xem `evidence/11-dashboard-overview.html`. |
| `pytest` | 22 passed | 23 passed (CP1) | Bổ sung kiểm tra CCCD và thẻ thanh toán. |
| Số traces hợp lệ | 0 | Ít nhất 16 root traces (CP2) | Evidence `06-trace-list.png` cho thấy 16 root traces, mỗi trace có agent/retriever/generation observations. |
| Số PII leak | 0 | 0 (CP1) | `validate_logs.py` không phát hiện email, SĐT VN, CCCD hoặc thẻ thô. |
| Latency P95 / TTFT P95 | 151 ms / 50 ms (CP2 workload) | Chưa chạy | 20 response trong cửa sổ dashboard hiện tại. |
| Retrieval success rate | 100% (CP2 workload) | Chưa chạy | 20 retrieval thành công trong cửa sổ dashboard hiện tại. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa contextvars ở đầu request, dùng header `x-request-id` nếu có hoặc sinh `req-<8-hex>`, bind vào structlog context và trả lại qua `x-request-id`; latency của middleware được trả qua `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** `user_id_hash` (SHA-256 rút gọn), `session_id`, `feature`, `model`, `env`, cùng event, timestamp và `correlation_id`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` duyệt toàn bộ event payload và redact string trước cả JSON renderer và JSONL file processor. Rules xử lý email, số điện thoại Việt Nam, CCCD và thẻ thanh toán.
- **Cách kiểm chứng kết quả:** Workload 10 request tạo 10 correlation ID khác nhau; `validate_logs.py` đạt 100/100, không phát hiện PII thô. Xem `evidence/02-log-validator.txt`, `evidence/04-structured-log.txt` và `evidence/05-pii-redaction.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Workload do app cục bộ chạy đã tạo ít nhất 16 root traces trong project Langfuse cá nhân. `evidence/06-trace-list.png` hiển thị root observations và các child observations agent, retriever, generation.
- **Cấu trúc root/retrieval/generation observations:** Code tạo root `lab-agent-run`, child retriever `retrieval` và child generation `llm-generation`. Generation có model, managed prompt link khi có, token usage và cost; input/output được lưu dạng preview đã redact để không đưa PII lên trace.
- **Cách nối trace với log:** `correlation_id` được đặt trong trace metadata của root, retriever và generation, đồng thời có trong structured log.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Version 1: `baseline`, sau rollback là `production`.
- **Version/label candidate:** Version 2: `candidate` và `latest`; prompt thêm yêu cầu trả lời trong tối đa hai câu.
- **Trace ID của mỗi version:** v1/production: `a1fdc7c8fffb015b2ba9de8a495df82c`; v2/candidate: `57c4ad7f8027fd90754ae611f2d61fdc`; v2/production: `6872b375ea7022ccaaf3918303885e6a`; v1/production sau rollback: `3db6201a760479c967038c9f11cc9834`. Correlation IDs tương ứng là `req-prompt-v1-check`, `req-prompt-v2-candidate`, `req-prompt-v2-production` và `req-prompt-v1-rollback-ok`.
- **Trace metadata evidence:** Trace `6389d6bad39697d046682ccb2399f4a5` dùng correlation ID `req-correlation-evidence`; ảnh waterfall hiển thị correlation ID và span tree tại `evidence/07-trace-waterfall.png`, còn ảnh generation có prompt v1, model, token và cost tại `evidence/08-trace-metadata.png`.
- **Cách promote và rollback `production`:** Đã chuyển `production` từ v1 sang v2, tạo request `req-prompt-v2-production`, sau đó chuyển `production` về v1 và retry thành công bằng `req-prompt-v1-rollback-ok`. Xem `evidence/09-prompt-versions.png` và `evidence/10-prompt-rollback.png`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `scripts/render_dashboard.py` render đúng sáu panel từ `data/logs.jsonl`: latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality. Snapshot CP2 có P95 latency 151 ms, TTFT P95 50 ms, error rate 0%, retrieval success 100%, total cost $0.037368 và quality mean 0.88.
- **SLO và lý do chọn:** `fast_successful_requests` đặt mục tiêu 99.5% request hoàn thành trong 3000 ms trên cửa sổ 28 ngày, cùng ngưỡng P95 trên dashboard để theo dõi tail latency nhìn thấy được.
- **Cách tính error budget:** 0.5% × 28 × 24 × 60 = 201.6 phút. Request lỗi hoặc response vượt 3000 ms tiêu thụ budget.
- **Ba alert và runbook tương ứng:** `high_request_error_rate` (critical, >2% trong 5 phút), `latency_slo_breach` (warning, P95 >3000 ms trong 10 phút), và `retrieval_success_degradation` (warning, <90% trong 5 phút); xem `config/alert_rules.yaml` và `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
