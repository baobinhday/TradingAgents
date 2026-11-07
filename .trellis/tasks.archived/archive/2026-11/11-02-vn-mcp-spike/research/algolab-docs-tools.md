# 3. Công cụ & hàm

Algolab MCP có **12 công cụ** trong danh sách của AI (10 công cụ dữ liệu + `search` + `call_function`) và **danh mục chuyên sâu** gọi qua `call_function`. Nhóm công cụ giao dịch chỉ hiện với khoá đã bật quyền giao dịch — xem [Giao dịch qua MCP](/docs/trading).

## 3.1 Công cụ trực tiếp

### get_market_overview

**Tổng quan thị trường** — toàn cảnh thị trường trong một lượt: chỉ số, độ rộng, dẫn dắt, khối ngoại, phái sinh, tổng kết phiên.

Toàn cảnh thị trường chứng khoán Việt Nam trong MỘT lượt: chỉ số (điểm, % thay đổi, P/E–P/B), top tăng/giảm, độ rộng kỹ thuật, 5 mã RS dẫn đầu, combo tín hiệu đang khớp, khối ngoại toàn thị trường, hợp đồng phái sinh gần nhất và bản tổng kết phiên mới nhất.

Dùng khi: "thị trường hôm nay", "VN-Index thế nào", cần bối cảnh trước khi phân tích mã. · Không dùng khi: cần chuỗi giá (→ get_price_history) hoặc khối ngoại từng mã chi tiết (→ call_function get_foreign_flows_detail).

Tham số: as_of (YYYY-MM-DD, mặc định phiên mới nhất — ngày cũ thì điểm và P/E–P/B đúng phiên đó); index (mặc định VNINDEX; VN30, HNX, UPCOM…).

Kết quả: chỉ số tính điểm; giá trị VND; khối lượng cổ phiếu; trong phiên là số realtime.

Xem thêm: get_technical_signals, get_news, get_intelligence.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `as_of` | string = null | Ngày YYYY-MM-DD; mặc định phiên mới nhất (số realtime trong phiên). |
| `index` | string = "VNINDEX" | Chỉ số chính: VNINDEX (mặc định), VN30, HNX, UPCOM, VN100… |

Ví dụ:

```
get_market_overview()
```

### get_price_history

**Lịch sử giá (nến)** — nến OHLCV mọi mã, khung 1 phút đến 1 tháng.

Chuỗi nến OHLCV của một mã bất kỳ: cổ phiếu (từ 2013), ETF, chứng quyền, chỉ số (từ 2013), phái sinh liên tục VN30F1M/VN30F2M (lưu từ 2017) hoặc từng hợp đồng; khung ngày/tuần/tháng và phút–giờ (cổ phiếu 50 phiên gần nhất có nến ATC 14:45, phái sinh từ 04/2026, chỉ số ~55 phiên gần nhất). Truy vấn được toàn bộ lịch sử.

Dùng khi: xu hướng, hỗ trợ/kháng cự, hiệu suất theo thời gian, khối ngoại theo ngày của một mã. · Không dùng khi: chỉ cần giá hiện tại (→ get_quotes).

Tham số: symbol; interval 1m|5m|15m|30m|1h|1d|1w|1mo; from_date/to_date; limit (mặc định 250, tối đa 1000); cursor lấy trang CŨ hơn.

Kết quả: bars dạng bảng, limit nến MỚI NHẤT, cũ trước mới sau; nến ngày là giá điều chỉnh (VND), có cổ tức/chia thưởng sau đó thì kèm c_actual = giá khớp thực tế; nến phút là giá thô; cổ phiếu kèm khối ngoại ròng, sự kiện quyền; chỉ số kèm pe, pb theo ngày.

Xem thêm: get_company_profile, get_technical_signals.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string (bắt buộc) | Mã bất kỳ: cổ phiếu (HPG), ETF, chứng quyền, chỉ số (VNINDEX, VN30), phái sinh (VN30F1M, VN30F2M hoặc mã hợp đồng). |
| `interval` | 1m\|5m\|15m\|30m\|1h\|1d\|1w\|1mo = "1d" | Khung nến: 1m, 5m, 15m, 30m, 1h, 1d (mặc định), 1w, 1mo. |
| `from_date` | string = null | Từ ngày YYYY-MM-DD (tuỳ chọn). |
| `to_date` | string = null | Đến ngày YYYY-MM-DD; mặc định hôm nay. |
| `limit` | integer = 250 | Số nến MỚI NHẤT cần lấy (mặc định 250, tối đa 1000). |
| `cursor` | string = null | meta.next_cursor của lượt trước để lấy tiếp các nến CŨ hơn. |

Ví dụ:

```
get_price_history(symbol="HPG", interval="1d", limit=120)
```

### get_quotes

**Giá realtime nhiều mã** — giá realtime tối đa 50 mã một lượt (cổ phiếu, CW, ETF, chỉ số, phái sinh).

Giá realtime của tối đa 50 mã trong MỘT lượt — cổ phiếu, ETF, chứng quyền, chỉ số và phái sinh (kể cả VN30F1M/VN30F2M): giá khớp, % thay đổi, khối lượng, tốc độ khớp (RVOL), basis và OI phái sinh.

Dùng khi: "giá HPG bây giờ", so sánh nhanh nhiều mã, soi danh mục. · Không dùng khi: cần lịch sử (→ get_price_history) hoặc hồ sơ doanh nghiệp (→ get_company_profile).

Tham số: symbols — danh sách mã, vd ["HPG","VN30F1M","VNINDEX"].

Kết quả: mỗi mã một dòng; giá VND, chỉ số và phái sinh tính điểm; updated_at theo giờ sàn.

Xem thêm: get_market_overview, get_price_history.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbols` | list[string] (bắt buộc) | Danh sách mã (tối đa 50), vd ["HPG","VN30F1M","VNINDEX"]. |

Ví dụ:

```
get_quotes(symbols=["HPG", "VCB", "VNINDEX"])
```

### get_company_profile

**Hồ sơ doanh nghiệp** — hồ sơ, sở hữu, định giá tự tính, hiệu suất, giá mục tiêu của một doanh nghiệp.

Hồ sơ một doanh nghiệp niêm yết: thông tin chung và ngành ICB 4 cấp, cơ cấu sở hữu, định giá (P/E, P/B, EPS, BVPS do AlgolabX tự tính với số cổ phiếu đúng thời điểm, kèm số của nhà cung cấp), hiệu suất giá, thanh khoản, giá mục tiêu đồng thuận CTCK và AlgolabX, sự kiện quyền/cổ tức.

Dùng khi: "HPG là công ty gì", "định giá VCB", bắt đầu phân tích một mã. · Không dùng khi: cần số liệu BCTC chi tiết (→ get_financial_statements).

Tham số: symbol; sections — chọn trong overview, ownership, valuation, performance, targets, events (mặc định tất cả trừ events).

Kết quả: mỗi section một khối; tiền VND, tỷ lệ % (hậu tố _pct).

Xem thêm: get_financial_statements, get_research_reports.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string (bắt buộc) | Mã cổ phiếu hoặc ETF, vd HPG. |
| `sections` | list[overview\|ownership\|valuation\|performance\|targets\|events] = null | Chọn trong overview, ownership, valuation, performance, targets, events; mặc định tất cả trừ events. |

Ví dụ:

```
get_company_profile(symbol="HPG")
```

### get_financial_statements

**Báo cáo tài chính** — BCTC theo mẫu ngành (KQKD, CĐKT, LCTT) + dự phóng AlgolabX.

Báo cáo tài chính theo đúng mẫu ngành (doanh nghiệp, ngân hàng, chứng khoán, bảo hiểm) của hơn 1.500 mã từ 2016: kết quả kinh doanh, cân đối kế toán, lưu chuyển tiền tệ theo quý hoặc năm; KQKD kèm dự phóng các quý tới của AlgolabX (tách riêng, không trộn với số đã công bố).

Dùng khi: tăng trưởng doanh thu/lợi nhuận, biên lợi nhuận, nợ vay, dòng tiền. · Không dùng khi: chỉ cần P/E, P/B, vốn hoá (→ get_company_profile).

Tham số: symbol; statement income|balance|cash (mặc định income); period quarter|annual; limit số kỳ (mặc định 8, tối đa 20); detail summary (dòng chính) | full (cả cây).

Kết quả: lines dạng bảng dòng × kỳ, đơn vị tỷ VND; dòng EPS tính đồng.

Xem thêm: search(kind="field") để tra mã chỉ tiêu.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string (bắt buộc) | Mã cổ phiếu, vd VCB. |
| `statement` | income\|balance\|cash = "income" | income = KQKD (mặc định), balance = cân đối kế toán, cash = lưu chuyển tiền tệ. |
| `period` | quarter\|annual = "quarter" | quarter (mặc định) hoặc annual. |
| `limit` | integer = 8 | Số kỳ gần nhất (mặc định 8, tối đa 20). |
| `detail` | summary\|full = "summary" | summary = dòng chính (cấp 1–2 + EPS); full = toàn bộ cây kèm dòng cha. |

Ví dụ:

```
get_financial_statements(symbol="VCB", statement="income", limit=4)
```

### get_research_reports

**Báo cáo phân tích CTCK** — báo cáo 50 CTCK + AlgolabX, đồng thuận giá mục tiêu, upside.

Báo cáo phân tích của 50 CTCK và AlgolabX (gần 7.000 báo cáo từ 2022): danh sách kèm khuyến nghị, giá mục tiêu và link đọc; khi có symbol thì kèm đồng thuận giá mục tiêu, khuyến nghị mới nhất của từng CTCK, AlgolabX theo kỳ hạn và upside so với giá hiện tại.

Dùng khi: "CTCK nói gì về VCB", "giá mục tiêu HPG", báo cáo ngành/vĩ mô mới. · Không dùng khi: cần đọc toàn văn (→ call_function get_report_content với id).

Tham số: symbol; broker (vd SSI, VCI, HSC, ALGOLABX); from_date; limit (mặc định 20); cursor.

Kết quả: reports dạng bảng; giá VND; url là trang đọc trên algolab.vn — dùng link này khi dẫn nguồn.

Xem thêm: get_company_profile.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string = null | Mã cổ phiếu — kèm đồng thuận giá mục tiêu và upside. |
| `broker` | string = null | Mã CTCK, vd SSI, VCI, HSC, MBS, ALGOLABX. |
| `from_date` | string = null | Từ ngày YYYY-MM-DD. |
| `limit` | integer = 20 | Số báo cáo mỗi trang (mặc định 20, tối đa 100). |
| `cursor` | string = null | meta.next_cursor của lượt trước. |

Ví dụ:

```
get_research_reports(symbol="VCB", limit=10)
```

### get_news

**Tin tức** — tin doanh nghiệp có sentiment, tổng kết phiên, tin trong phiên.

Tin tức chứng khoán Việt Nam: tin doanh nghiệp kèm chấm điểm sentiment (Tích cực/Trung tính/Tiêu cực), bản tổng kết phiên cuối ngày và bản tin cập nhật trong phiên của AlgolabX; khi có symbol thì lọc theo mã.

Dùng khi: "tin mới về HPG", "hôm nay thị trường có gì", tìm chất xúc tác/rủi ro. · Không dùng khi: cần báo cáo phân tích (→ get_research_reports).

Tham số: symbol; kind company|recap|intraday|expert (recap + intraday); from_date; limit (mặc định 20 tin doanh nghiệp / 5 bản tin, tối đa 100); cursor.

Kết quả: items mới nhất trước; published_at dạng ISO.

Xem thêm: get_market_overview.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string = null | Lọc theo mã. |
| `kind` | company\|recap\|intraday\|expert = "company" | company = tin doanh nghiệp có sentiment (mặc định); recap = tổng kết cuối ngày; intraday = bản tin trong phiên; expert = recap + intraday. |
| `from_date` | string = null | Từ thời điểm (YYYY-MM-DD hoặc ISO datetime). |
| `limit` | integer = null | Số mục (mặc định 20 tin doanh nghiệp / 5 bản tin; tối đa 100). |
| `cursor` | string = null | meta.next_cursor của lượt trước. |

Ví dụ:

```
get_news(symbol="HPG", limit=10)
```

### get_technical_signals

**Tín hiệu kỹ thuật** — RS đa khung, MACD, bắt đáy, độ rộng, combo tín hiệu đã backtest.

Phân tích kỹ thuật định lượng của AlgolabX: xếp hạng sức mạnh giá RS đa khung, MACD, tín hiệu bắt đáy, beta, độ lệch chuẩn lợi suất; độ rộng thị trường; các combo tín hiệu đã backtest từ 2020 (tỉ lệ thắng, lợi suất vượt VN-Index) kèm danh sách mã đang khớp hôm nay.

Dùng khi: tìm mã mạnh/yếu, xác nhận xu hướng, quét cơ hội theo bằng chứng lịch sử. · Không dùng khi: cần chuỗi giá (→ get_price_history).

Tham số: symbol (một mã) hoặc top (mặc định 20, tối đa 200); as_of; min_adtv (sàn thanh khoản VND, mặc định 10 tỷ); detail summary|full.

Kết quả: tickers dạng bảng (RS là percentile 0–100, lợi suất %); signal_combos; market_breadth.

Xem thêm: get_market_overview.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string = null | Một mã — trả riêng phân tích của mã đó (bỏ qua top/min_adtv). |
| `as_of` | string = null | Ngày YYYY-MM-DD; mặc định phiên mới nhất. |
| `top` | integer = 20 | Số mã RS mạnh nhất (mặc định 20, tối đa 200). |
| `min_adtv` | number = 10000000000.0 | Sàn thanh khoản — GTGD trung bình 1 tháng (VND), mặc định 10 tỷ; 0 = không lọc. |
| `detail` | summary\|full = "summary" | summary = cột chính; full = mọi khung RS/beta/độ lệch chuẩn và mọi combo. |

Ví dụ:

```
get_technical_signals(top=20)
```

### get_macro

**Vĩ mô nhanh** — vĩ mô Việt Nam & thế giới (14 chuỗi chính) + FedWatch.

Vĩ mô nhanh: Việt Nam (CPI, GDP, M2, tỷ giá trung tâm, IIP, bán lẻ) và thế giới (vàng, dầu Brent/WTI, S&P 500, Nasdaq, lợi suất TPCP Mỹ 10 năm, DXY, USD/VND) kèm FedWatch — xác suất Fed cắt/giữ/tăng lãi suất các kỳ họp tới.

Dùng khi: bối cảnh vĩ mô, tác động tỷ giá/lãi suất lên thị trường. · Không dùng khi: cần chỉ tiêu khác — kho có hơn 1.300 chỉ tiêu (→ search kind="macro" rồi call_function get_macro_series).

Tham số: scope vietnam|world|all; symbols (vd ["CPI","GOLD"]); from_date/to_date; limit số quan sát MỚI NHẤT mỗi chuỗi (mặc định 24).

Kết quả: series có latest, previous và obs dạng bảng; fed_outlook.

Xem thêm: call_function browse_macro; pha chu kỳ kinh tế → get_economic_cycle.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `scope` | vietnam\|world\|all = "all" | vietnam, world hoặc all (mặc định). |
| `symbols` | list[string] = null | Lọc chuỗi — Việt Nam: CPI, GDP, M2, FX, IIP, RETAIL; thế giới: GOLD, BRENT, WTI, SP500, NASDAQ, US10Y, DXY, USDVND. |
| `from_date` | string = null | Từ ngày YYYY-MM-DD. |
| `to_date` | string = null | Đến ngày YYYY-MM-DD. |
| `limit` | integer = 24 | Số quan sát MỚI NHẤT mỗi chuỗi (mặc định 24, tối đa 500). |

Ví dụ:

```
get_macro(scope="all")
```

### get_intelligence

**★ AlgolabX Intelligence** — ★ dự báo VN-Index các tháng tới, tín hiệu phái sinh 4 mô hình, danh mục AlgolabX (độc quyền).

★ Sản phẩm độc quyền AlgolabX (không phải dữ liệu thô): dự báo VN-Index các tháng tới (đường dự báo + dải tin cậy 50/80/95%) kèm luận điểm và kịch bản — cập nhật định kỳ, không phải mỗi phiên (gọi tên bản theo edition_date, không theo as_of); tín hiệu phái sinh VN30F từ 4 mô hình (xu hướng, hồi quy, carry, chênh lệch); 5 danh mục do PM AlgolabX quản lý theo triết lý đầu tư (tỷ trọng, luận điểm, hiệu suất).

Dùng khi: "VN-Index cuối năm bao nhiêu", "AlgolabX đang nghĩ gì", khẩu vị rủi ro trung hạn. · Không dùng khi: cần giá hiện tại (→ get_quotes).

Tham số: as_of (mặc định bản mới nhất); section — đọc toàn văn một mục luận điểm (số mục hoặc từ khoá); detail summary|full.

Kết quả: forecast (chỉ số chính + đường dự báo lấy mẫu, điểm), thesis (tóm tắt + mục lục), derivatives_signals, suggested_portfolios — tham khảo, không phải khuyến nghị cá nhân.

Xem thêm: get_market_overview, get_economic_cycle.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `as_of` | string = null | Ngày bản dự báo YYYY-MM-DD; mặc định bản mới nhất. |
| `detail` | summary\|full = "summary" | summary (mặc định) = đường dự báo lấy mẫu + tóm tắt luận điểm + mục lục; full = toàn bộ (luận điểm rất dài, có thể bị cắt ở 200 KB). |
| `section` | string = null | Đọc toàn văn MỘT mục luận điểm: số mục (vd "1", "I.1", "III.B.2") hoặc từ khoá tiêu đề (vd "tín dụng"); xem thesis.sections. |

Ví dụ:

```
get_intelligence()
```

### search

**Tìm dữ liệu** — tìm hàm, mã, ngành, chỉ tiêu BCTC, chỉ tiêu vĩ mô (có/không dấu).

Tìm mọi thứ trong kho dữ liệu Algolab bằng từ khoá tiếng Việt (có/không dấu) hoặc tiếng Anh: hàm dữ liệu (kèm tham số và ví dụ gọi), mã chứng khoán (toàn bộ mã đang niêm yết: cổ phiếu, ETF, chứng quyền, phái sinh, chỉ số), ngành ICB, chỉ tiêu BCTC (hơn 3.300), chỉ tiêu vĩ mô (hơn 1.300).

Dùng khi: không chắc tên mã/hàm/chỉ tiêu; muốn biết Algolab có dữ liệu gì về một chủ đề. · Không dùng khi: đã biết công cụ cần gọi.

Tham số: query; kind auto|function|symbol|sector|field|macro; limit (mặc định 10).

Kết quả: nhóm functions / symbols / sectors / fields / macro; hàm danh mục gọi qua call_function.

Xem thêm: call_function.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `query` | string (bắt buộc) | Từ khoá tiếng Việt (có hoặc không dấu) hoặc tiếng Anh, vd "lãi suất liên ngân hàng", "Hoà Phát", "chứng quyền", "CPI". |
| `kind` | auto\|function\|symbol\|sector\|field\|macro = "auto" | auto (mặc định, mọi loại) · function · symbol · sector · field (chỉ tiêu BCTC) · macro. |
| `limit` | integer = 10 | Số kết quả mỗi nhóm (mặc định 10, tối đa 50). |

Ví dụ:

```
search(query="lãi suất liên ngân hàng")
```

### call_function

**Gọi hàm chuyên sâu** — chạy hàm trong danh mục chuyên sâu theo tên.

Chạy một hàm trong danh mục dữ liệu chuyên sâu của Algolab theo tên, với tham số dạng object. Sai tên → gợi ý tên gần nhất; sai tham số → trả danh sách tham số và ví dụ đúng.

Dùng khi: cần dữ liệu ngoài 10 công cụ chính (danh mục bên dưới). · Không dùng khi: công cụ trực tiếp đã đủ.

Tham số: name; arguments (object).

Kết quả: cùng dạng {status, data, meta} như mọi công cụ.

Xem thêm: search.

Ví dụ: call_function(name="get_warrants", arguments={"underlying": "HPG"}).

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `name` | string (bắt buộc) | Tên hàm trong danh mục, vd "get_warrants". |
| `arguments` | object = null | Tham số của hàm dạng object, vd {"underlying": "HPG"}. |

Ví dụ:

```
call_function(name="get_warrants", arguments={"underlying": "HPG"})
```

## 3.2 Danh mục chuyên sâu (qua call_function)

### get_index_intraday

**Chuỗi điểm chỉ số trong phiên** — chuỗi điểm trong phiên của chỉ số (mỗi phút).

Chuỗi điểm trong phiên của một chỉ số (điểm cuối mỗi phút, các phiên trong 5 ngày gần nhất; nến phút lâu hơn → get_price_history interval="1m") kèm giá trị hiện tại và định giá P/E–P/B của chính chỉ số.

Dùng khi: cần diễn biến chi tiết từng thời điểm trong phiên. · Không dùng khi: cần nến phút/giờ gọn (→ get_price_history interval="5m") hoặc chỉ cần điểm hiện tại (→ get_quotes).

Tham số: index (mặc định VNINDEX); from_date, to_date (ngày hoặc ISO datetime).

Kết quả: points dạng bảng {ts (giờ VN), value, change, change_pct, volume}.

Xem thêm: get_market_overview.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `index` | string = "VNINDEX" | Mã chỉ số, vd VNINDEX, VN30, HNX, UPCOM. |
| `from_date` | string = null | Từ (YYYY-MM-DD hoặc ISO datetime); mặc định 3 ngày gần nhất. |
| `to_date` | string = null | Đến (YYYY-MM-DD hoặc ISO datetime); mặc định hiện tại. |

Ví dụ:

```
call_function(name="get_index_intraday", arguments={"index": "VN30"})
```

### get_foreign_flows_detail

**Khối ngoại toàn thị trường** — khối ngoại toàn thị trường một phiên, top mua/bán ròng.

Khối ngoại toàn thị trường một phiên: tổng mua/bán/ròng (khối lượng, giá trị) và xếp hạng các mã bị bán ròng / được mua ròng mạnh nhất; phiên đang chạy trả số trong phiên.

Dùng khi: "khối ngoại hôm nay bán ròng mã nào", tiền ngoại đang dồn vào đâu. · Không dùng khi: cần khối ngoại theo ngày của MỘT mã (→ get_price_history, cột foreign_net).

Tham số: date (YYYY-MM-DD, mặc định phiên mới nhất); top (mặc định 20, tối đa 50).

Kết quả: khối lượng cổ phiếu, giá trị VND (âm = bán ròng); value_is_estimate cho biết có phần ước tính.

Xem thêm: get_market_overview.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `date` | string = null | Phiên YYYY-MM-DD; mặc định phiên mới nhất (số trong phiên nếu đang giao dịch). |
| `top` | integer = 20 | Số mã mỗi chiều mua/bán ròng (mặc định 20, tối đa 50). |

Ví dụ:

```
call_function(name="get_foreign_flows_detail", arguments={"top": 10})
```

### get_corporate_events

**Sự kiện quyền & cổ tức** — sự kiện quyền, cổ tức, ĐHCĐ, giao dịch nội bộ của một mã.

Sự kiện quyền và cổ tức của một mã: cổ tức tiền (đồng/cp) và cổ phiếu (%), đại hội cổ đông, phát hành, công bố KQKD, giao dịch nội bộ, thay đổi sở hữu.

Dùng khi: "HPG chia cổ tức khi nào", "TCX chia cổ phiếu chưa", lịch sự kiện sắp tới, giải thích biến động giá quanh ngày GDKHQ. · Không dùng khi: cần tin tức (→ get_news).

Tham số: symbol; from_date (mặc định 12 tháng trước); to_date (mặc định 6 tháng tới).

Kết quả: events theo ngày tăng dần.

Xem thêm: get_company_profile, get_price_history.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbol` | string (bắt buộc) | Mã cổ phiếu, vd HPG. |
| `from_date` | string = null | Từ ngày YYYY-MM-DD; mặc định 12 tháng trước. |
| `to_date` | string = null | Đến ngày YYYY-MM-DD; mặc định 6 tháng tới. |

Ví dụ:

```
call_function(name="get_corporate_events", arguments={"symbol": "HPG"})
```

### list_symbols

**Danh sách mã** — danh sách mã theo loại, sàn, ngành ICB.

Danh sách mã chứng khoán lọc theo loại (cổ phiếu, ETF, chứng quyền, phái sinh, chỉ số), sàn, tiền tố hoặc ngành ICB cấp 1–4 (tên có/không dấu, Việt hoặc Anh); cổ phiếu xếp theo vốn hoá.

Dùng khi: "các mã ngành ngân hàng", "chứng quyền đang lưu hành", lấy danh sách để so sánh. · Không dùng khi: tìm một mã theo tên công ty (→ search kind="symbol").

Tham số: kind (mặc định stock); exchange HOSE|HNX|UPCOM; prefix; sector + icb_level (mặc định 2); limit (mặc định 100, tối đa 2000); cursor.

Kết quả: symbols dạng bảng + total.

Xem thêm: search, get_quotes.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `kind` | stock\|etf\|cw\|futures\|index\|all = "stock" | stock (mặc định), etf, cw, futures (kể cả VN30F1M/F2M), index, all. |
| `exchange` | HOSE\|HNX\|UPCOM = null | Lọc theo sàn. |
| `prefix` | string = null | Tiền tố mã, vd VN. |
| `sector` | string = null | Tên ngành ICB (có/không dấu, Việt hoặc Anh), vd "Ngân hàng". |
| `icb_level` | integer = 2 | Cấp ngành ICB của sector: 1 (rộng) … 4 (chi tiết). |
| `limit` | integer = 100 | Số mã mỗi trang (mặc định 100, tối đa 2000). |
| `cursor` | string = null | meta.next_cursor của lượt trước. |

Ví dụ:

```
call_function(name="list_symbols", arguments={"sector": "Ngân hàng", "limit": 30})
```

### screen_stocks

**Lọc cổ phiếu** — lọc cổ phiếu theo định giá, sinh lời, hiệu suất giá, RS, thanh khoản, khối ngoại, ngành, cờ tín hiệu.

Lọc cổ phiếu đang niêm yết: điều kiện AND trên chỉ tiêu, sàn, ngành ICB, cờ tín hiệu phiên gần nhất; P/E, P/B do AlgolabX tự tính.

Dùng khi: "cổ phiếu P/E dưới 10, ROE trên 15%", "ngân hàng tăng mạnh nhất 3 tháng", "mã có tín hiệu P/E rẻ hơn lịch sử". · Không dùng khi: xem chi tiết một mã (→ get_company_profile).

Tham số: conditions — [{field, op (>, >=, <, <=, =, between), value}], field: price, change_pct, market_cap, pe, pb, eps_ttm, roe, roa, gross_margin, net_margin, debt_to_equity, revenue_growth_yoy, profit_growth_yoy, return_1w, return_1m, return_3m, return_6m, return_ytd, return_1y, rs_score, rs_1m, rs_3m, adtv_1m, foreign_net_value; exchange HOSE|HNX|UPCOM; sector; flags (khoá cờ, sai → gợi ý); sort_by, order; limit (mặc định 50, tối đa 500); cursor.

Kết quả: stocks dạng bảng (mã, tên, sàn, ngành + chỉ tiêu đã lọc/sắp) + total; đơn vị ở meta.units.

Xem thêm: get_company_profile, get_technical_signals, list_symbols.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `conditions` | list[Condition] = [] | Điều kiện AND, vd [{"field": "pe", "op": "<", "value": 10}]. |
| `exchange` | HOSE\|HNX\|UPCOM = null | Lọc theo sàn. |
| `sector` | string = null | Tên ngành ICB cấp bất kỳ (có/không dấu), vd "Ngân hàng", "Thép". |
| `flags` | list[string] = [] | Cờ tín hiệu phải có (AND), vd ["pe_cheap", "macd_cross_up"]. |
| `sort_by` | price\|change_pct\|market_cap\|pe\|pb\|eps_ttm\|roe\|roa\|gross_margin\|net_margin\|debt_to_equity\|revenue_growth_yoy\|profit_growth_yoy\|return_1w\|return_1m\|return_3m\|return_6m\|return_ytd\|return_1y\|rs_score\|rs_1m\|rs_3m\|adtv_1m\|foreign_net_value = null | Sắp theo chỉ tiêu (mặc định market_cap). |
| `order` | desc\|asc = "desc" | desc (mặc định) hoặc asc. |
| `limit` | integer = 50 | Số mã mỗi trang (mặc định 50, tối đa 500). |
| `cursor` | string = null | meta.next_cursor của lượt trước. |

Ví dụ:

```
call_function(name="screen_stocks", arguments={"conditions": [{"field": "pe", "op": "<", "value": 10}, {"field": "roe", "op": ">", "value": 15}], "sort_by": "roe", "limit": 20})
```

### get_sector_valuation

**Định giá theo ngành** — P/E, P/B, ROE trung vị và P/E gia quyền theo ngành ICB; lọc sàn, rổ VN30, vốn hoá; xem từng mã một ngành.

Định giá theo ngành ICB từ P/E, P/B do AlgolabX tự tính: mỗi ngành có số DN, P/E trung vị, P/E gia quyền (Σ vốn hoá / Σ LNST cổ đông mẹ 4 quý, chỉ DN có lãi), P/B trung vị, ROE trung vị, tổng vốn hoá. Trung vị P/E loại P/E ≤ 0 và P/E > 100.

Dùng khi: "ngành nào đang có P/E thấp nhất", "so sánh định giá nhóm ngân hàng trong VN30", "P/E trung vị ngành thép". · Không dùng khi: lọc mã theo nhiều chỉ tiêu (→ screen_stocks); định giá một mã (→ get_company_profile).

Tham số: level (cấp ICB 1–4, mặc định 2); exchange HOSE|HNX|UPCOM; index VN30; sector (một ngành → từng mã kèm P/E, P/B, ROE, vốn hoá); min_market_cap (tỷ VND); sort (pe_median mặc định, pe_weighted, pb_median, roe_median, market_cap_total, n); order.

Kết quả: sectors (hoặc summary + stocks khi có sector); vốn hoá tỷ VND, ROE %; meta.as_of = ngày định giá.

Xem thêm: screen_stocks, list_symbols, get_company_profile.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `level` | integer = null | Cấp ngành ICB: 1 (rộng) … 4 (chi tiết); mặc định 2 — cấp "ngành" của bảng giá Algolab. |
| `exchange` | HOSE\|HNX\|UPCOM = null | Chỉ tính mã trên một sàn. |
| `index` | VN30 = null | Chỉ tính mã trong rổ chỉ số — hiện có VN30 (rổ HOSE đang hiệu lực). |
| `sector` | string = null | Một ngành (tên có/không dấu, Việt hoặc Anh), vd "Ngân hàng", "Thép" → trả từng mã của ngành kèm P/E, P/B, ROE, vốn hoá. |
| `min_market_cap` | number = null | Vốn hoá tối thiểu (tỷ VND), vd 1000. |
| `sort` | pe_median\|pe_weighted\|pb_median\|roe_median\|market_cap_total\|n = "pe_median" | Sắp theo pe_median (mặc định), pe_weighted, pb_median, roe_median, market_cap_total, n. |
| `order` | asc\|desc = null | Mặc định: định giá (P/E, P/B) thấp → cao; ROE, vốn hoá, n cao → thấp. |

Ví dụ:

```
call_function(name="get_sector_valuation", arguments={"sort": "pe_median"})
```

### get_report_content

**Toàn văn báo cáo** — toàn văn báo cáo phân tích (markdown) theo id.

Toàn văn một báo cáo phân tích dạng markdown (bảng số liệu giữ nguyên) kèm khuyến nghị, giá mục tiêu, link PDF — không cần tải PDF.

Dùng khi: tóm tắt, so sánh, trích số liệu từ một báo cáo cụ thể. · Không dùng khi: chưa có id (→ get_research_reports trước).

Tham số: report_id (id từ get_research_reports); part (mặc định 1 — báo cáo dài chia phần ~60.000 ký tự).

Kết quả: content markdown của phần đó, part/parts (còn phần sau thì gọi part kế tiếp), content_source, pdf_url.

Xem thêm: get_research_reports.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `report_id` | integer (bắt buộc) | id báo cáo lấy từ get_research_reports. |
| `part` | integer = 1 | Phần thứ mấy — báo cáo dài chia phần ~60.000 ký tự; kết quả ghi part/parts. |

Ví dụ:

```
call_function(name="get_report_content", arguments={"report_id": 12345})
```

### get_stock_style

**Phong cách đầu tư cổ phiếu** — hộp phong cách 3x3 (Lớn/Vừa/Nhỏ × Giá trị/Cân bằng/Tăng trưởng), điểm V/G và 8 factor z-score theo mã.

Phong cách đầu tư của từng cổ phiếu theo mô hình AlgolabX, cập nhật hằng tuần: ô quy mô (Lớn/Vừa/Nhỏ) × phong cách (Giá trị/Cân bằng/Tăng trưởng), điểm giá trị V và tăng trưởng G (0–100 trong hàng quy mô), net = G − V, 8 factor z-score (size, value, momentum, quality, lowvol, liquidity, dividend, foreign), độ phủ dữ liệu, cùng ngưỡng vốn hoá chia Lớn/Vừa/Nhỏ của tuần.

Dùng khi: "HPG là cổ phiếu giá trị hay tăng trưởng", "mã nào cùng ô phong cách". · Không dùng khi: cần chỉ số định giá P/E, P/B (→ screen_stocks, get_sector_valuation) hoặc hiệu suất phong cách theo pha (→ get_economic_cycle section=style).

Tham số: symbols (danh sách mã cổ phiếu, tối đa 50).

Kết quả: data.stocks bảng {columns, rows} (symbol, week, size, style, v_score, g_score, net, net_sn, z_size … z_foreign, coverage, in_universe), data.breakpoints (cap_lm, cap_ms tỷ VND); meta.notes giải thích thang đo và liệt kê mã không có dữ liệu — mô tả, không phải khuyến nghị.

Xem thêm: get_economic_cycle, get_knowledge, screen_stocks.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `symbols` | list[string] (bắt buộc) | Danh sách mã cổ phiếu (tối đa 50), vd ["HPG","VCB"]. |

Ví dụ:

```
call_function(name="get_stock_style", arguments={"symbols": ["HPG", "VCB"]})
```

### get_warrants

**Chứng quyền** — bảng giá chứng quyền kèm giá thực hiện, đáo hạn, ITM/OTM, hoà vốn.

Bảng giá chứng quyền có bảo đảm realtime kèm đặc tả: mã cơ sở, tổ chức phát hành, giá thực hiện, tỷ lệ chuyển đổi, ngày đáo hạn, số ngày còn lại, giá cơ sở hiện tại, trạng thái ITM/ATM/OTM, điểm hoà vốn.

Dùng khi: "chứng quyền của HPG", CW thanh khoản nhất, chọn CW theo moneyness. · Không dùng khi: cần lịch sử giá CW (→ get_price_history).

Tham số: underlying (mã cơ sở) hoặc symbol (một CW); limit (mặc định 60, tối đa 200), sắp theo giá trị giao dịch.

Kết quả: warrants dạng bảng; giá VND.

Xem thêm: get_quotes.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `underlying` | string = null | Mã cơ sở, vd HPG — liệt kê CW của mã đó. |
| `symbol` | string = null | Một mã CW cụ thể, vd CHPG2608. |
| `limit` | integer = 60 | Số CW tối đa (mặc định 60, tối đa 200), sắp theo giá trị giao dịch. |

Ví dụ:

```
call_function(name="get_warrants", arguments={"underlying": "HPG"})
```

### get_derivatives_snapshot

**Phái sinh realtime** — mọi hợp đồng tương lai: giá, basis, OI, CVD mua/bán chủ động.

Ảnh chụp realtime mọi hợp đồng tương lai chỉ số đang giao dịch: giá, % thay đổi, basis so với chỉ số cơ sở, OI, khối lượng, giá chào mua/bán tốt nhất, hợp đồng tháng gần; kèm CVD mua/bán chủ động VN30F 5 phiên gần nhất.

Dùng khi: "basis phái sinh hôm nay", vị thế phe mua/bán chủ động. · Không dùng khi: cần lịch sử (→ get_price_history symbol="VN30F1M").

Tham số: không có.

Kết quả: contracts dạng bảng (điểm, hợp đồng); orderflow_cvd.

Xem thêm: get_quotes, get_intelligence.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| — | — | Không có tham số |

Ví dụ:

```
call_function(name="get_derivatives_snapshot", arguments={})
```

### browse_macro

**Duyệt cây chỉ tiêu vĩ mô** — duyệt cây chỉ tiêu vĩ mô theo nhóm.

Duyệt cây chỉ tiêu vĩ mô Việt Nam + thế giới theo nhóm: không tham số → danh sách nhóm (tăng trưởng, lạm phát, lãi suất, tỷ giá, thương mại, đầu tư, ngân sách, lao động, BĐS CBRE, hàng hoá…); category → đầu cây của nhóm; parent_key → các chỉ tiêu con.

Dùng khi: muốn biết Algolab có những chỉ tiêu vĩ mô nào về một chủ đề. · Không dùng khi: đã biết tên chỉ tiêu (→ search kind="macro").

Tham số: category; parent_key; region.

Kết quả: items {key, name, unit, is_group, has_children}; dùng key với get_macro_series.

Xem thêm: get_macro_series.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `category` | string = null | Nhóm, vd growth, inflation, rates, fx, trade, investment, budget, labor, gia, housing. |
| `parent_key` | string = null | key của một nhóm để xem chỉ tiêu con. |
| `region` | string = null | Lọc vùng, vd VN. |

Ví dụ:

```
call_function(name="browse_macro", arguments={"category": "rates"})
```

### get_macro_series

**Chuỗi chỉ tiêu vĩ mô** — chuỗi số liệu một chỉ tiêu vĩ mô bất kỳ theo key.

Chuỗi số liệu của MỘT chỉ tiêu vĩ mô bất kỳ trong kho hơn 1.300 chỉ tiêu (lưu từ 1985, có cả số dự báo) theo key; truy vấn được toàn bộ lịch sử, đặt to_date ở tương lai để lấy số dự báo.

Dùng khi: cần lịch sử một chỉ tiêu cụ thể (lãi suất liên ngân hàng, FDI, xuất khẩu, giá thép…). · Không dùng khi: chưa có key (→ search kind="macro" hoặc browse_macro).

Tham số: key; from_date, to_date; limit số quan sát MỚI NHẤT (mặc định 90, tối đa 2000).

Kết quả: obs dạng bảng {date, value} tăng dần; unit, frequency.

Xem thêm: get_macro.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `key` | string (bắt buộc) | key chỉ tiêu (từ search kind="macro" hoặc browse_macro). |
| `from_date` | string = null | Từ ngày YYYY-MM-DD. |
| `to_date` | string = null | Đến ngày YYYY-MM-DD. |
| `limit` | integer = 90 | Số quan sát MỚI NHẤT (mặc định 90, tối đa 2000). |

Ví dụ:

```
call_function(name="get_macro_series", arguments={"key": "vn-cpi-yoy-headline-cpi-yoy", "limit": 24})
```

### get_economic_cycle

**★ Chu kỳ kinh tế & luân chuyển ngành** — ★ pha chu kỳ kinh tế Việt Nam (đồng hồ đầu tư), ngành thắng theo pha, xếp hạng 19 ngành, vòng xoay ngành, tâm lý thị trường.

★ Mô hình AlgolabX: Việt Nam đang ở pha nào của chu kỳ kinh tế (Phục hồi · Tăng trưởng nóng · Đình lạm · Suy giảm) theo động lượng tăng trưởng G và lạm phát I; ngành HOSE thắng ở mỗi pha; xếp hạng 19 ngành; vòng xoay ngành; tâm lý thị trường; tín hiệu phân bổ chiến thuật (taa); phong cách theo pha (style).

Dùng khi: "kinh tế đang ở pha nào", "ngành nào hưởng lợi giai đoạn này", "nên lệch tỷ trọng cổ phiếu bao nhiêu". · Không dùng khi: cần số liệu vĩ mô thô (→ get_macro) hay phong cách từng mã (→ get_stock_style).

Tham số: section summary (mặc định) | history | playbook | outlook | rotation | assessment | scorecard | sentiment | taa (dòng mới nhất + 60 phiên) | style | all (8 phần đầu); months; phase; days.

Kết quả: bảng {columns, rows}; meta.notes nêu phương pháp, độ tươi — tham khảo, không phải khuyến nghị.

Xem thêm: get_stock_style, get_macro, get_sector_valuation, get_intelligence.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `section` | summary\|history\|playbook\|outlook\|rotation\|assessment\|scorecard\|sentiment\|taa\|style\|all = "summary" | summary (mặc định: pha hiện tại, đồng hồ, động lực, ngành dẫn/đuối) · history (pha từng tháng) · playbook (sổ tay pha 10 ngành HOSE × 4 pha) · outlook (xếp hạng 19 ngành) · rotation (vòng xoay ngành theo tuần) · assessment (bài đánh giá tháng) · scorecard (chấm điểm xếp hạng) · sentiment (tâm lý thị trường) · taa (tín hiệu phân bổ chiến thuật cổ phiếu vs trái phiếu/vàng: dòng mới nhất + 60 phiên) · style (chỉ số phong cách giá trị/tăng trưởng/quy mô theo pha hiện tại, 2 hệ pha quadrant + cfa) · all (8 phần đầu). |
| `months` | integer = 24 | Số tháng gần nhất cho history, assessment, scorecard (mặc định 24, tối đa 200). |
| `phase` | string = null | Lọc một pha (history, playbook, assessment, scorecard): recovery, overheat, stagflation, reflation hoặc tên Việt "Phục hồi", "Tăng trưởng nóng", "Đình lạm", "Suy giảm". |
| `days` | integer = 30 | Số phiên gần nhất cho sentiment (mặc định 30, tối đa 365). |

Ví dụ:

```
call_function(name="get_economic_cycle", arguments={"section": "summary"})
```

### get_knowledge

**Kiến thức quản lý danh mục (CFA L3)** — tra cứu khái niệm: IPS, phân bổ tài sản, hành lang tái cân bằng, phong cách value/growth, factor, chu kỳ kinh tế, đo hiệu suất, phái sinh, đạo đức.

Kho kiến thức quản lý danh mục nền tảng CFA Level III do Algolab viết lại bằng lời riêng (không phải giáo trình chép nguyên văn, không phải khuyến nghị): IPS, phân bổ tài sản chiến lược, hành lang tái cân bằng, hộp phong cách value/growth, factor, chu kỳ kinh tế, đo hiệu suất, phái sinh, đạo đức, thị trường tư nhân.

Dùng khi: câu hỏi khái niệm/phương pháp ("hành lang tái cân bằng là gì"). · Không dùng khi: cần số liệu thị trường thật (→ get_economic_cycle cho pha chu kỳ hiện tại).

Tham số: query (câu hỏi/khái niệm, có/không dấu); ref (lấy đúng một đoạn theo ref từ lượt trước); k số đoạn tối đa (mặc định 5, tối đa 8).

Kết quả: bảng {ref, title, text}; meta.notes nhắc đây là kiến thức nền, không phải khuyến nghị.

Xem thêm: search, get_economic_cycle.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `query` | string = null | Câu hỏi/khái niệm, vd "hành lang tái cân bằng", "hộp phong cách 3x3". |
| `ref` | string = null | Lấy đúng một đoạn theo ref (vd từ lượt gọi query trước). |
| `k` | integer = 5 | Số đoạn tối đa (mặc định 5, tối đa 8) — bỏ qua khi có ref. |

Ví dụ:

```
call_function(name="get_knowledge", arguments={"query": "hành lang tái cân bằng"})
```

### get_quota

**Hạn mức khoá API** — hạn mức của khoá đang dùng: đã dùng, còn lại, giờ đặt lại.

Hạn mức của khoá đang dùng: gói, số lượt đã dùng hôm nay / hạn mức ngày, còn lại, giới hạn tốc độ mỗi phút, giờ đặt lại; free và lite dùng chung một pool toàn hệ thống.

Dùng khi: người dùng hỏi về quota, hạn mức, vì sao bị chặn. · Không dùng khi: cần dữ liệu thị trường.

Tham số: không có.

Kết quả: plan_code, daily_quota, used_today, remaining, rate_limit_per_minute, reset_at.

Xem thêm: https://algolab.vn/account/upgrade.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| — | — | Không có tham số |

Ví dụ:

```
call_function(name="get_quota", arguments={})
```

### report_issue

**Báo lỗi cho Algolab** — báo lỗi hoặc dữ liệu sai cho đội AlgolabX, kèm ngữ cảnh lượt gọi gần nhất.

Gửi báo cáo lỗi / dữ liệu sai cho đội AlgolabX; máy chủ tự đính kèm tối đa 10 lượt gọi gần nhất của khoá (tên hàm, tham số, mã lỗi) để tái hiện.

Dùng khi: một hàm lỗi lặp lại (INTERNAL, UPSTREAM_ERROR, TIMEOUT), số liệu rõ ràng sai, thiếu dữ liệu, người dùng muốn góp ý. · Không dùng khi: lỗi tham số (INVALID_ARGUMENT) — sửa theo error.hint.

Tham số: description (10–2000 ký tự); function (tuỳ chọn); severity low|normal|high.

Kết quả: id báo cáo + status received. Tối đa 5 báo cáo mỗi giờ.

Xem thêm: get_quota.

| Tham số | Kiểu & mặc định | Mô tả |
|---|---|---|
| `description` | string (bắt buộc) | Mô tả lỗi: làm gì, mong đợi gì, nhận được gì (vd số liệu sai, lỗi lặp lại). |
| `function` | string = null | Tên hàm liên quan (tuỳ chọn), vd get_quotes. |
| `severity` | low\|normal\|high = "normal" | low · normal (mặc định) · high. |

Ví dụ:

```
call_function(name="report_issue", arguments={"description": "get_quotes trả giá HPG = 0 trong phiên sáng 25/09", "function": "get_quotes", "severity": "normal"})
```

## 3.3 Quy ước kết quả

Mọi công cụ trả một khối JSON:

```
{"status": "ok", "data": {...}, "meta": {"function": "get_price_history", "source": "...", "as_of": "...",
 "units": {...}, "count": 250, "next_cursor": null, "truncated": false, "related": [...], "quota": {"used": 12, "limit": 1000}}}
```

- `status`: ok · partial (một phần nguồn lỗi, vẫn có dữ liệu) · empty (hợp lệ nhưng không có dữ liệu) · error.
- Bảng (≥ 5 dòng) trả dạng `{columns, rows}`; object con nhỏ làm phẳng thành cột `cha.con`.
- Phân trang: truyền nguyên `meta.next_cursor` vào tham số `cursor`, giữ các tham số khác.
- Tham số vượt trần bị **kẹp** và ghi trong `meta.clamped`; kết quả quá 200 KB bị cắt (`meta.truncated`).

| Mã lỗi | Ý nghĩa |
|---|---|
| `INVALID_ARGUMENT` | Tham số sai — hint có ví dụ gọi đúng |
| `SYMBOL_NOT_FOUND` | Không có mã — thử search(kind="symbol") |
| `FUNCTION_NOT_FOUND` | Không có hàm/công cụ — hint gợi ý tên gần nhất |
| `NOT_FOUND` | Không có bản ghi (báo cáo, chỉ tiêu…) |
| `FORBIDDEN` | Không đủ quyền (vd công cụ giao dịch) |
| `TIMEOUT` | Truy vấn quá thời gian — thu hẹp khoảng ngày/giảm limit |
| `UPSTREAM_ERROR` | Nguồn dữ liệu tạm lỗi — thử lại sau |
| `INTERNAL` | Lỗi nội bộ — kèm mã tham chiếu |
| `RATE_LIMITED` | Vượt tốc độ/phút — chờ 60 giây |
| `QUOTA_EXCEEDED` | Hết hạn mức ngày — đặt lại 00:00 giờ VN |