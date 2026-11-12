# Dự báo mực nước hồ thủy điện Sông Ba Hạ

Mã nguồn của báo cáo thực tập doanh nghiệp: **Xây dựng đề cương nghiên cứu bài toán dự báo mực nước về hồ thủy điện**.

- **Tác giả:** [Phạm Văn Đức]
- **Giảng viên hướng dẫn:** [Lê Hồng Anh]

## Giới thiệu

Dự án dự báo mực nước thượng lưu hồ Sông Ba Hạ từ số liệu quan trắc theo giờ giai đoạn 2022–2025, ở 5 hạn dự báo: **1, 6, 24, 72 và 168 giờ**. Các mô hình được so sánh với mốc **Persistence** (lấy mực nước hiện tại làm dự báo):

- Học máy: Random Forest, XGBoost
- Học sâu: LSTM, GRU

## Cấu trúc thư mục

| File / thư mục | Nội dung |
|---|---|
| `DuBao_MucNuoc_SBH_Phan1.ipynb` | Phần 1: tiền xử lý, phân tích khám phá dữ liệu (EDA), xây dựng đặc trưng |
| `DuBao_MucNuoc_SBH_Phan2_DeHieu.ipynb` | Phần 2: huấn luyện, so sánh và đánh giá các mô hình |
| `sbh_prep.py` | Hàm đọc và tiền xử lý dữ liệu dùng chung cho hai notebook |
| `ket_qua_so_sanh.csv` | Bảng kết quả so sánh các mô hình |
| `figs/` | Hình EDA (chuỗi thời gian, tính mùa, tương quan, độ trễ mưa, tự tương quan, cân bằng nước) |
| `figs2/` | Hình kết quả mô hình (thực đo và dự báo, sai số theo hạn, sai số theo mức nước, đặc trưng quan trọng) |
| `requirements.txt` | Danh sách thư viện cần cài |

## Dữ liệu

Dữ liệu vận hành thật của hồ (35.064 dòng, bước 1 giờ, từ 01/01/2022 đến 31/12/2025) **không được công bố** trong repository này.

Để chạy lại, đặt file `raw_data_sbh.csv` cùng thư mục với notebook. File cần có:

| Nhóm | Cột |
|---|---|
| Thời gian | `time` |
| Mực nước | `H_tl`, `H_dbt`, `H_c` |
| Lưu lượng | `Q_ve`, `Sigma_Qx`, `Q_xt`, `Q_xm` |
| Vận hành | `N_cxs`, `N_cxm` |
| Khí tượng | nhiệt độ, độ ẩm, lượng mưa, tốc độ gió, hướng gió, mây tầng giữa, áp suất, độ ẩm đất (0–7 cm) |

## Cách chạy

```bash
pip install -r requirements.txt
jupyter notebook
```

Chạy lần lượt notebook Phần 1, sau đó Phần 2. LSTM và GRU nên chạy trên máy có GPU hoặc Google Colab.

## Phương pháp tóm tắt

- **Chia dữ liệu theo thời gian:** năm 2025 làm tập kiểm tra; có đoạn đệm theo hạn dự báo để chống rò rỉ thông tin.
- **47 đặc trưng:** mực nước và lưu lượng ở các độ trễ, thống kê trượt, mưa tích lũy, mùa vụ.
- **Biến mục tiêu:** các mô hình cây dự báo mức thay đổi mực nước ΔZ = Z(t+h) − Z(t).
- **Chỉ số đánh giá:** MAE, RMSE, R², NSE, mức cải thiện so với Persistence.

## Kết quả

RMSE (m) trên tập kiểm tra năm 2025, số in đậm là tốt nhất:

| Mô hình | 1 giờ | 6 giờ | 24 giờ | 72 giờ | 168 giờ |
|---|---|---|---|---|---|
| Persistence | 0,038 | 0,102 | 0,261 | 0,565 | 0,862 |
| Random Forest | **0,036** | **0,085** | **0,241** | 0,561 | 0,792 |
| XGBoost | 0,056 | 0,088 | 0,252 | 0,525 | 0,802 |
| LSTM | 0,038 | 0,100 | 0,248 | 0,538 | 0,790 |
| GRU | 0,037 | 0,098 | 0,242 | **0,518** | **0,755** |

Nhận xét chính:

- Các mô hình chỉ cải thiện vừa phải so với Persistence.
- Random Forest tốt nhất ở hạn ngắn (1, 6, 24 giờ), GRU tốt nhất ở hạn dài (72, 168 giờ).
- Mùa lũ khó dự báo hơn mùa kiệt; dự báo hạn một tuần còn hạn chế (NSE tốt nhất khoảng 0,31).

Bảng đầy đủ các chỉ số trong `ket_qua_so_sanh.csv`.

## Hạn chế

- Chỉ có một năm kiểm tra (2025), có một trận lũ lớn; thứ hạng mô hình có thể thay đổi ở năm khác.
- LSTM và GRU chạy một lần, chưa kiểm tra độ ổn định theo hạt giống ngẫu nhiên.
- Chưa có đường quan hệ Z–V và dự báo mưa; mưa chỉ là số liệu tại một điểm khí tượng.
- Mô hình chỉ có giá trị tham khảo, không thay thế quy trình vận hành hồ chứa.
