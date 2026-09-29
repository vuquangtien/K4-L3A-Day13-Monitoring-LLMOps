# Alert runbook

Mỗi alert đo một triệu chứng người dùng hoặc một SLI, không báo động theo tên implementation nội bộ.

## Alert 1: high request error rate

- Severity: critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack `#day13-llmops-alerts`
- SLI/SLO liên quan: error rate tối đa 2%; các request lỗi tiêu thụ error budget của SLO `fast_successful_requests`.
- Điều kiện: `error_rate_pct > 2` trong 5 phút.
- Ảnh hưởng tới người dùng: request chat thất bại hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xác định khoảng thời gian và `error_type` trong panel Errors.
  2. Lọc `request_failed` trong `data/logs.jsonl`, lấy một `correlation_id` và kiểm tra log trước đó của cùng request.
  3. Mở trace cùng correlation ID; kiểm tra retrieval và generation span có lỗi hay không.
- Mitigation tạm thời: disable incident hoặc dependency lỗi nếu đây là practice; giảm traffic/feature bị ảnh hưởng và retry có kiểm soát sau khi dependency hồi phục.
- Owner: LLMOps on-call.

## Alert 2: latency SLO breach

- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack `#day13-llmops-alerts`
- SLI/SLO liên quan: P95 latency phải không vượt 3000 ms; slow request làm SLI `fast_successful_requests` trở thành bad event.
- Điều kiện: `latency_p95_ms > 3000` trong 10 phút.
- Ảnh hưởng tới người dùng: chat phản hồi chậm, có thể dẫn đến abandon hoặc timeout ở client.
- Ba bước kiểm tra đầu tiên:
  1. Xác định P95/P99 và khoảng thời gian tăng ở panel Latency/TTFT.
  2. Lọc `response_sent` chậm trong log và lấy correlation ID.
  3. So sánh waterfall trace: retrieval span, generation span và TTFT để khoanh vùng bottleneck.
- Mitigation tạm thời: disable incident/feature gây chậm, giảm concurrency hoặc cache kết quả retrieval khi phù hợp.
- Owner: LLMOps on-call.

## Alert 3: retrieval success degradation

- Severity: warning
- Duration: 5 phút liên tục
- Kênh thông báo: Slack `#day13-llmops-alerts`
- SLI/SLO liên quan: retrieval success rate tối thiểu 90%; retrieval không thành công làm chất lượng câu trả lời giảm.
- Điều kiện: `retrieval_success_rate_pct < 90` trong 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời thiếu ngữ cảnh hoặc request bị lỗi khi dependency retrieval không sẵn sàng.
- Ba bước kiểm tra đầu tiên:
  1. Xem retrieval success và error breakdown trong panel Errors.
  2. Lọc `request_failed` có `tool_name=retrieval` để lấy correlation ID.
  3. Xem retriever observation trong trace để xác định timeout, lỗi hay không có document.
- Mitigation tạm thời: kiểm tra health/kết nối vector store, chuyển sang fallback answer an toàn hoặc tắt feature retrieval bị ảnh hưởng.
- Owner: Retrieval service owner.
