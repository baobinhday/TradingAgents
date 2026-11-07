# 2. Bản đồ dữ liệu

Số liệu cập nhật 02/11/2026 — tự làm mới hằng ngày.

## 1. Thị trường & chỉ số

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Chỉ số realtime | 29 chỉ số HOSE/HNX/UPCOM: điểm, thay đổi, khối lượng; P/E, P/B của chính chỉ số do AlgolabX tự tính | phiên hiện tại; nến phút 3 phiên | ~1 giây trong phiên | get_market_overview · get_quotes · get_index_intraday |
| Độ rộng & dẫn dắt | Top tăng/giảm, độ rộng MACD/bắt đáy toàn sàn, 5 mã RS dẫn đầu, combo tín hiệu đang khớp | phiên gần nhất | trong phiên / cuối ngày | get_market_overview |
| Khối ngoại toàn thị trường | Mua/bán/ròng toàn sàn, top mã mua/bán ròng; trong phiên cập nhật liên tục | từ 01/2024 | liên tục; chốt ~08:00 hôm sau | get_market_overview · get_foreign_flows_detail |

## 2. Giá & giao dịch

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Giá ngày OHLCV | 3.581 mã (cổ phiếu, ETF, chứng quyền, chỉ số) — giá điều chỉnh, kèm khối ngoại theo mã | 01/2013 → nay | realtime + chốt cuối phiên | get_price_history |
| Nến phút 1m → 1h | Cổ phiếu (có nến ATC 14:45), phái sinh VN30F1M/F2M, chỉ số | 50 phiên gần nhất | mỗi phút trong phiên | get_price_history |
| Giá realtime | Giá khớp, % thay đổi, khối lượng, tốc độ khớp (RVOL) — tối đa 50 mã một lượt | phiên hiện tại | ~1 giây | get_quotes |

## 3. Doanh nghiệp

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Hồ sơ & sở hữu | Ngành ICB 4 cấp, vốn hoá, sở hữu nước ngoài/nhà nước/nội bộ, free-float | hiện tại | hằng ngày | get_company_profile |
| Định giá AlgolabX tự tính | P/E, P/B, EPS TTM, BVPS theo số cổ phiếu đúng thời điểm; trung vị P/E, P/B, ROE theo ngành ICB | hằng ngày | cuối phiên | get_company_profile · get_sector_valuation |
| Sự kiện quyền & cổ tức | Cổ tức tiền/cổ phiếu, ĐHCĐ, phát hành, KQKD, giao dịch nội bộ | 12 tháng qua + sắp tới | hằng ngày | get_company_profile · get_corporate_events |
| Danh sách mã & ngành | Lọc theo sàn, loại, ngành ICB; tìm theo tên không dấu | hiện tại | hằng ngày | search · list_symbols |

## 4. Báo cáo tài chính & dự phóng

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| BCTC theo mẫu ngành | 1.536 mã; mẫu doanh nghiệp / ngân hàng / chứng khoán / bảo hiểm; KQKD, cân đối, lưu chuyển tiền tệ | 2016 → Q3/2026 | khi doanh nghiệp công bố | get_financial_statements |
| Dự phóng AlgolabX | 124 mã: doanh thu, lợi nhuận các quý tới | các quý tới | theo báo cáo AlgolabX | get_financial_statements |
| Từ điển chỉ tiêu | 3.370 chỉ tiêu BCTC, tên Việt/Anh | — | — | search(kind="field") |

## 5. Báo cáo phân tích & khuyến nghị

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Báo cáo CTCK | 7.906 báo cáo của 53 CTCK + AlgolabX: doanh nghiệp, ngành, vĩ mô | 03/2022 → nay | hằng ngày | get_research_reports |
| Toàn văn | 5.665 báo cáo có toàn văn markdown (không cần tải PDF) | như trên | hằng ngày | get_report_content |
| Giá mục tiêu & đồng thuận | Đồng thuận CTCK, khuyến nghị mới nhất từng CTCK, AlgolabX theo kỳ hạn, upside | 12 tháng gần nhất | hằng ngày | get_research_reports · get_company_profile |

## 6. Tin tức

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Tin doanh nghiệp | 3.014 tin gắn mã, chấm điểm sentiment | gần đây | liên tục | get_news |
| Tổng kết phiên | 179 bản tổng kết cuối ngày của AlgolabX | hằng ngày | sau giờ đóng cửa | get_news(kind="recap") |
| Tin trong phiên | 1.662 bản tin chuyên gia trong phiên | hằng ngày | trong phiên | get_news(kind="intraday") |

## 7. Kỹ thuật & tín hiệu

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Sức mạnh giá RS | Xếp hạng percentile RS 1D → 5Y, beta, độ lệch chuẩn lợi suất | từ 02/2020 | cuối phiên | get_technical_signals |
| MACD & bắt đáy | 63.492 tín hiệu theo mã | từ 02/2020 | 09:10 và 15:35 | get_technical_signals |
| Cờ tín hiệu & backtest | 565.959 cờ tín hiệu; combo đã backtest (tỉ lệ thắng, vượt VN-Index) | từ 02/2020 | 16:40 | get_technical_signals |

## 8. Phái sinh & chứng quyền

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| HĐTL VN30 liên tục | VN30F1M/VN30F2M: OHLC, OI, basis, giá điều chỉnh roll | 08/2017 → nay | trong phiên / cuối ngày | get_price_history · get_quotes |
| Hợp đồng & dòng lệnh | 24 hợp đồng đang niêm yết, CVD mua/bán chủ động 5 phiên | hiện tại | realtime | get_derivatives_snapshot |
| Chứng quyền | 528 mã CW: giá thực hiện, tỷ lệ, đáo hạn, ITM/OTM, hoà vốn | hiện tại | realtime | get_warrants |

## 9. Vĩ mô

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Vĩ mô Việt Nam & thế giới | 1.376 chỉ tiêu, 364.289 quan sát: tăng trưởng, lạm phát, lãi suất, tỷ giá, thương mại, FDI, ngân sách, lao động, BĐS (CBRE), hàng hoá | 1985 → dự báo 2027 | theo kỳ công bố | get_macro · browse_macro · get_macro_series |
| FedWatch | Xác suất Fed cắt/giữ/tăng lãi suất các kỳ họp tới (tự tính từ hợp đồng ZQ) | hiện tại | hằng ngày | get_macro |

## 10. ★ AlgolabX Intelligence (độc quyền)

| Dữ liệu | Mô tả | Lịch sử | Cập nhật | Công cụ / hàm |
|---|---|---|---|---|
| Dự báo VN-Index | 28.100 điểm dữ liệu dự báo qua 119 bản: đường dự báo các tháng tới, dải tin cậy 50/80/95%, luận điểm, kịch bản | từ 12/2025 | định kỳ (119 bản từ 12/2025), không phải mỗi phiên | get_intelligence |
| Tín hiệu phái sinh 4 mô hình | Xu hướng, hồi quy, carry, chênh lệch — Long/Short hôm nay so với hôm trước | hiện tại | hằng ngày | get_intelligence |
| Danh mục mô hình | 5 danh mục PM AlgolabX theo triết lý đầu tư (Vega, Sirius, Orion, Polaris, Kochab): tỷ trọng, thẻ luận điểm, hiệu suất, alpha, Sharpe | đang công bố | hằng ngày | get_intelligence |
| Chu kỳ kinh tế & luân chuyển ngành | Pha chu kỳ kinh tế Việt Nam theo tháng trên đồng hồ đầu tư (Phục hồi · Tăng trưởng nóng · Đình lạm · Suy giảm), sổ tay pha 10 ngành HOSE, xếp hạng triển vọng 19 ngành, vòng xoay ngành theo tuần, bài đánh giá tháng, tâm lý thị trường | pha từ 2014, sổ tay pha từ 2016 | pha: hằng tháng · xếp hạng: hằng ngày | get_economic_cycle |

## Cách dùng

- 10 công cụ trực tiếp trả lời phần lớn câu hỏi trong 1–2 lượt gọi.
- Dữ liệu chuyên sâu: `search(query=…)` tìm hàm/mã/chỉ tiêu (kèm ví dụ gọi) → `call_function(name=…, arguments={…})`.
- Mọi kết quả có dạng `{status, data, meta}`; bảng dạng `{columns, rows}`; lỗi có `error.code` + `error.hint`.