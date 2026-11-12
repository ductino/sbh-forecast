"""
sbh_prep.py — Hàm dùng chung cho bài dự báo mực nước hồ Sông Ba Hạ (Phần 1 -> Phần 2).
Nội dung giống Phần 1: đọc & làm sạch dữ liệu, tạo đặc trưng, chia theo thời gian.
"""
import numpy as np
import pandas as pd

MNC, MNDBT = 101.0, 105.0
MAX_INTERP_HOURS = 6
HORIZONS = [1, 6, 24, 72, 168]
TRAIN_END = "2023-12-31 23:00"
VAL_END = "2024-12-31 23:00"
FLOOD_MONTHS = [9, 10, 11, 12]


def fill_short_gaps(s: pd.Series, max_gap: int = MAX_INTERP_HOURS, method: str = "interp") -> pd.Series:
    """Chỉ điền các đoạn thiếu <= max_gap giờ; đoạn dài hơn giữ nguyên NaN hoàn toàn."""
    isna = s.isna()
    grp = (isna != isna.shift()).cumsum()
    gap_len = isna.groupby(grp).transform("sum")           # độ dài đoạn NaN chứa từng điểm
    if method == "interp":
        filled = s.interpolate(method="time", limit_area="inside")   # nội suy tuyến tính theo thời gian
    else:
        filled = s.ffill()                                           # điền tiến cho biến rời rạc
    return s.where(~(isna & (gap_len <= max_gap)), filled)


def load_clean(path: str) -> pd.DataFrame:
    """Đọc CSV, đổi tên cột, loại ngoại lai vật lý, nội suy khoảng thiếu ngắn (<= 6 giờ).
    Các đoạn thiếu dài hơn 6 giờ được giữ nguyên NaN (các mẫu liên quan bị loại ở bước chia dữ liệu)."""
    df = pd.read_csv(path, parse_dates=["time"], encoding="utf-8-sig").set_index("time")
    df = df.rename(columns={
        "Temperature (°C)": "Temp", "Humidity (%)": "Humid", "Precipitations (mm)": "Rain",
        "Wind_speeds (km/h)": "WindSp", "Wind_direction (°)": "WindDir",
        "Cloud_cover_mid (%)": "Cloud", "Pressure (hPa)": "Press",
        "Soil_moisture_0_7cm (m³/m³)": "SoilM"}).drop(columns=["ten_ho"])

    # Ngoại lai vật lý: mực nước thấp hơn MNC quá 1 m hoặc cao hơn MNDBT quá 3 m
    bad = (df["H_tl"] < MNC - 1.0) | (df["H_tl"] > MNDBT + 3.0)
    df.loc[bad, "H_tl"] = np.nan
    for c in ["Q_ve", "Sigma_Qx", "Q_xt", "Q_xm"]:
        df.loc[df[c] < 0, c] = np.nan

    cont = ["H_tl", "Q_ve", "Sigma_Qx", "Q_xt", "Q_xm"]
    disc = ["N_cxs", "N_cxm"]
    for c in cont:
        df[c] = fill_short_gaps(df[c], method="interp")
    for c in disc:
        df[c] = fill_short_gaps(df[c], method="ffill")

    df["H_dbt"], df["H_c"] = MNDBT, MNC
    df["is_flood"] = df.index.month.isin(FLOOD_MONTHS).astype(int)
    return df


def make_features(data: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Bảng đặc trưng + mục tiêu cho hạn dự báo `horizon` giờ (chỉ dùng thông tin <= t)."""
    f = pd.DataFrame(index=data.index)
    lag_set = [1, 2, 3, 6, 12, 24, 48, 72, 168]
    f["H_now"] = data["H_tl"]
    for col in ["H_tl", "Q_ve", "Sigma_Qx"]:
        for l in lag_set:
            f[f"{col}_lag{l}"] = data[col].shift(l)
    f["Q_ve_now"] = data["Q_ve"]
    f["Qx_now"] = data["Sigma_Qx"]
    for l in [1, 6, 24]:
        f[f"dH_{l}"] = data["H_tl"] - data["H_tl"].shift(l)
    for w in [6, 24, 72, 168]:
        f[f"Rain_sum{w}"] = data["Rain"].rolling(w).sum()
    for w in [24, 72]:
        f[f"Qve_mean{w}"] = data["Q_ve"].rolling(w).mean()
    f["SoilM"] = data["SoilM"]
    f["Humid"] = data["Humid"]
    f["N_cxm"] = data["N_cxm"]
    f["hour_sin"] = np.sin(2 * np.pi * data.index.hour / 24)
    f["hour_cos"] = np.cos(2 * np.pi * data.index.hour / 24)
    f["month_sin"] = np.sin(2 * np.pi * data.index.month / 12)
    f["month_cos"] = np.cos(2 * np.pi * data.index.month / 12)
    f["is_flood"] = data["is_flood"]
    f["y_level"] = data["H_tl"].shift(-horizon)
    f["y_delta"] = f["y_level"] - f["H_now"]
    return f


def split_by_time(feat: pd.DataFrame, horizon: int):
    """Chia train/val/test theo thời gian, bỏ mẫu NaN, có purge `horizon` giờ ở cuối train/val."""
    feat = feat.dropna()
    t_tr, t_va = pd.Timestamp(TRAIN_END), pd.Timestamp(VAL_END)
    h = pd.Timedelta(hours=horizon)
    train = feat[feat.index + h <= t_tr]
    val = feat[(feat.index > t_tr) & (feat.index + h <= t_va)]
    test = feat[feat.index > t_va]
    return train, val, test


def feature_names(frame: pd.DataFrame):
    """Danh sách cột đặc trưng (bỏ các cột mục tiêu y_*)."""
    return [c for c in frame.columns if not c.startswith("y_")]