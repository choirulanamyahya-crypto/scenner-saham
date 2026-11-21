import streamlit as st
import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime

st.set_page_config(page_title="Auto Screener Saham IDX All-in-One", layout="wide")

st.title("📈 Auto Screener Saham IDX (All-in-One)")

# ==========================================
# SIDEBAR PENGATURAN
# ==========================================
st.sidebar.header("⚙️ Pengaturan Screener")

# Pilih Mode Analisa
mode_scan = st.sidebar.radio(
    "Pilih Mode Screening:",
    ["1. Breakout & Uptrend (Rumus Awal)", "2. Berburu Gorengan (Volume Spike)"]
)

# Auto-Scan Timer
auto_scan = st.sidebar.toggle("🔄 Aktifkan Auto-Scan Otomatis", value=False)
interval_menit = st.sidebar.selectbox(
    "Scan Ulang Setiap:",
    options=[5, 10, 15, 30],
    format_func=lambda x: f"{x} Menit",
    disabled=not auto_scan
)

st.sidebar.divider()

timeframe = st.sidebar.selectbox(
    "Timeframe Analisa",
    options=["5m", "15m", "1h", "1d"],
    index=1
)

# Parameter sesuai Mode yang dipilih
if mode_scan == "1. Breakout & Uptrend (Rumus Awal)":
    st.caption("Kriteria: Higher Low (HL) + Higher High (HH) + Tembus High Kemarin + Volume Makin Naik (Semua Saham)")
    jumlah_candle = st.sidebar.slider("Jumlah Candle Konfirmasi Naik", min_value=2, max_value=5, value=2)
    min_nilai_transaksi = st.sidebar.number_input("Minimal Nilai Transaksi (Juta Rp)", min_value=0, value=200, step=100)
else:
    st.caption("Kriteria: Harga Murah + Lonjakan Harga Cepat + Ledakan Volume (Khusus Gorengan/Volatilitas Tinggi)")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_harga = st.number_input("Harga Min (Rp)", min_value=1, value=51, step=10)
    with col2:
        max_harga = st.number_input("Harga Max (Rp)", min_value=50, value=1000, step=50)
    col3, col4 = st.sidebar.columns(2)
    with col3:
        min_naik_persen = st.number_input("Min Naik (%)", min_value=0.0, value=2.0, step=1.0)
    with col4:
        max_naik_persen = st.number_input("Max Naik (%)", min_value=1.0, value=20.0, step=1.0)
    min_vol_spike = st.sidebar.slider("Minimal Ledakan Volume (x Lipat)", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
    min_nilai_transaksi = st.sidebar.number_input("Minimal Nilai Transaksi (Juta Rp)", min_value=0, value=100, step=50)

st.sidebar.divider()

# Sumber Daftar Saham (Otomatis baca semua_saham.txt jika ada di GitHub/Folder)
opsi_sumber = ["Upload File .TXT (900+ Saham)", "150+ Saham Aktif & Gorengan", "Ketik Manual"]
if os.path.exists("semua_saham.txt"):
    opsi_sumber.insert(0, "Otomatis: semua_saham.txt (900+ Saham)")

sumber_saham = st.sidebar.radio("Pilih Sumber Saham:", opsi_sumber)

LIST_POPULER = (
    "BBCA, BBRI, BMRI, BBNI, BRIS, BBTN, BDMN, BNGA, NISP, ARTO, BBYB, BNBA, AGRO, BANK, BABP, "
    "TLKM, ISAT, EXCL, MTEL, TOWR, TBIG, FREN, ASII, AUTO, DRMA, ADRO, PTBA, ITMG, HRUM, INDY, "
    "DOID, BUMI, BYAN, KKGI, ABMM, BSSR, GEMS, ANTM, MDKA, INCO, MBMA, NCKL, TINS, BRMS, PSAB, "
    "ARCI, AMMN, BREN, CUAN, PTRO, PANI, TPIA, BRPT, CDIA, RATU, RAJA, MEDC, ENRG, ELSA, PGAS, "
    "AKRA, UNTR, GOTO, BUKA, BELI, EMTK, SCMA, MNCN, BHIT, KPIG, KLBF, SIDO, MIKA, HEAL, SILO, "
    "ICBP, INDF, MYOR, CMRY, CPIN, JPFA, MAIN, UNVR, AMRT, MIDI, MAPI, MAPA, ACES, ERAA, LPPF, "
    "RALS, CTRA, BSDE, SMRA, PWON, ASRI, DMAS, KIJA, BSML, JSMR, PTPP, WIKA, ADHI, WSKT, TOTL, "
    "INKP, TKIM, SMGR, INTP, DEWA, BFIN, SRTG, ASSA, BIRD, SMDR, TMAS, BULL, SOCI, SHIP, LEAD, "
    "WINS, ESSA, AVIA, CLEO, ULTJ, GOOD, HOKI, BOLA, WIFI, AWAN, CYBR, DATA, EDGE, DCII, MLPT, "
    "INET, NICO, NICE, STRK, GZCO, LSIP, AALI, DSNG, TAPG, SSMS, BWPT, SIMP, UNIQ, PACK, LABA"
)

tickers_final = []

if sumber_saham == "Otomatis: semua_saham.txt (900+ Saham)":
    with open("semua_saham.txt", "r", encoding="utf-8") as f:
        isi = f.read()
    isi_bersih = isi.replace(";", ",").replace("\n", ",").replace("\r", ",")
    raw = [x.strip().upper() for x in isi_bersih.split(",") if len(x.strip()) == 4 and x.strip().isalpha()]
    tickers_final = [f"{x}.JK" for x in set(raw)]
    st.sidebar.success(f"Otomatis memuat **{len(tickers_final)} saham**!")

elif sumber_saham == "Upload File .TXT (900+ Saham)":
    uploaded_file = st.sidebar.file_uploader("Upload semua_saham.txt", type=["txt", "csv"])
    if uploaded_file is not None:
        isi = uploaded_file.read().decode("utf-8")
        isi_bersih = isi.replace(";", ",").replace("\n", ",").replace("\r", ",")
        raw = [x.strip().upper() for x in isi_bersih.split(",") if len(x.strip()) == 4 and x.strip().isalpha()]
        tickers_final = [f"{x}.JK" for x in set(raw)]
        st.sidebar.success(f"Berhasil memuat **{len(tickers_final)} saham**!")
    else:
        st.sidebar.warning("Upload file semua_saham.txt dulu.")

elif sumber_saham == "150+ Saham Aktif & Gorengan":
    raw = [x.strip().upper() for x in LIST_POPULER.split(",") if x.strip()]
    tickers_final = [f"{x}.JK" for x in set(raw)]
    st.sidebar.info(f"Siap memindai **{len(tickers_final)} saham**.")

else:
    manual_input = st.sidebar.text_area("Ketik kode saham (pisahkan koma):", value="BUMI, DEWA, BRMS, CUAN, PTRO, PANI, GOTO")
    raw = [x.strip().upper() for x in manual_input.split(",") if x.strip()]
    tickers_final = [x if x.endswith(".JK") else f"{x}.JK" for x in set(raw)]

# ==========================================
# FUNGSI SCREENING
# ==========================================
def jalankan_screening(tickers, tf):
    periode = "5d" if tf in ["5m", "15m"] else ("1mo" if tf == "1h" else "3mo")
    chunk_size = 50
    total_chunks = (len(tickers) + chunk_size - 1) // chunk_size

    progress_bar = st.progress(0)
    status_text = st.empty()
    hasil = []

    for idx in range(total_chunks):
        batch = tickers[idx * chunk_size : (idx + 1) * chunk_size]
        status_text.text(f"⏳ Memindai antrean {idx + 1} dari {total_chunks} ({len(batch)} saham)...")

        try:
            data_all = yf.download(
                tickers=batch,
                period=periode,
                interval=tf,
                group_by="ticker",
                progress=False,
                threads=True
            )
        except Exception:
            continue

        for ticker in batch:
            try:
                df = data_all[ticker].dropna() if len(batch) > 1 else data_all.dropna()
                if len(df) < 7:
                    continue

                df['DateOnly'] = df.index.date
                unique_dates = sorted(df['DateOnly'].unique())
                if len(unique_dates) < 2:
                    continue

                tgl_kemarin = unique_dates[-2]
                df_kemarin = df[df['DateOnly'] == tgl_kemarin]
                high_kemarin = float(df_kemarin['High'].max())
                close_kemarin = float(df_kemarin['Close'].iloc[-1])

                harga_now = float(df['Close'].iloc[-1])
                vol_now = float(df['Volume'].iloc[-1])
                nilai_transaksi_juta = (harga_now * vol_now) / 1_000_000
                kode_bersih = ticker.replace(".JK", "")

                # LOGIKA MODE 1: RUMUS AWAL (HL + HH + BREAK D1 + VOL NAIK)
                if mode_scan == "1. Breakout & Uptrend (Rumus Awal)":
                    recent = df.tail(jumlah_candle)
                    lows = recent['Low'].values
                    highs = recent['High'].values
                    closes = recent['Close'].values
                    vols = recent['Volume'].values

                    is_hl = all(lows[i] > lows[i-1] for i in range(1, len(lows)))
                    is_hh = all(highs[i] > highs[i-1] for i in range(1, len(highs)))
                    is_break_d1 = harga_now > high_kemarin
                    is_vol_naik = all(vols[i] > vols[i-1] for i in range(1, len(vols)))

                    if is_hl and is_hh and is_break_d1 and is_vol_naik and (nilai_transaksi_juta >= min_nilai_transaksi):
                        persen_naik = ((closes[-1] - closes[-2]) / closes[-2]) * 100
                        persen_vol = ((vols[-1] - vols[-2]) / vols[-2]) * 100 if vols[-2] > 0 else 0
                        hasil.append({
                            "Emiten": kode_bersih,
                            "Harga": round(harga_now, 0),
                            "High Kemarin": round(high_kemarin, 0),
                            "Naik (%)": round(persen_naik, 2),
                            "Vol Naik (%)": round(persen_vol, 1),
                            "Transaksi (Jt)": round(nilai_transaksi_juta, 1),
                            "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{kode_bersih}"
                        })

                # LOGIKA MODE 2: GORENGAN (HARGA MURAH + VOLUME SPIKE)
                else:
                    if not (min_harga <= harga_now <= max_harga):
                        continue
                    naik_hari_ini = ((harga_now - close_kemarin) / close_kemarin) * 100 if close_kemarin > 0 else 0
                    if not (min_naik_persen <= naik_hari_ini <= max_naik_persen):
                        continue
                    avg_vol_prev = float(df['Volume'].iloc[-6:-1].mean())
                    if avg_vol_prev <= 0:
                        continue
                    vol_spike_ratio = vol_now / avg_vol_prev
                    if vol_spike_ratio < min_vol_spike or nilai_transaksi_juta < min_nilai_transaksi:
                        continue

                    status_break = "YA 🚀" if harga_now > high_kemarin else "Belum"
                    hasil.append({
                        "Emiten": kode_bersih,
                        "Harga": round(harga_now, 0),
                        "Naik Hari Ini (%)": round(naik_hari_ini, 2),
                        "Vol Spike (x)": round(vol_spike_ratio, 1),
                        "Transaksi (Jt)": round(nilai_transaksi_juta, 1),
                        "Break High D1": status_break,
                        "Chart": f"https://www.tradingview.com/chart/?symbol=IDX:{kode_bersih}"
                    })
            except Exception:
                continue

        progress_bar.progress((idx + 1) / total_chunks)
        time.sleep(0.4)

    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(hasil)

# ==========================================
# EKSEKUSI
# ==========================================
def tampilkan_hasil():
    if not tickers_final:
        st.error("Daftar saham kosong! Pilih sumber saham di menu kiri.")
        return

    df_hasil = jalankan_screening(tickers_final, timeframe)
    waktu_scan = datetime.now().strftime("%H:%M:%S WIB")

    if not df_hasil.empty:
        st.toast(f"Ketemu {len(df_hasil)} saham lolos!", icon="🚀")
        st.success(f"✅ Ditemukan **{len(df_hasil)} saham** dari {len(tickers_final)} saham! (Update: {waktu_scan})")
        sort_col = "Vol Naik (%)" if mode_scan.startswith("1.") else "Vol Spike (x)"
        df_hasil = df_hasil.sort_values(by=sort_col, ascending=False)
        st.dataframe(
            df_hasil,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Chart": st.column_config.LinkColumn("Cek Chart", display_text="Buka TradingView ↗")
            }
        )
    else:
        st.warning(f"Belum ada saham yang lolos kriteria saat ini. (Update: {waktu_scan})")

if auto_scan:
    st.info(f"🟢 **Auto-Scan AKTIF** — Scan ulang setiap **{interval_menit} menit**.")
    tampilkan_hasil()
    countdown_box = st.empty()
    for sisa in range(interval_menit * 60, 0, -1):
        menit, detik = divmod(sisa, 60)
        countdown_box.caption(f"⏱️ Scan otomatis berikutnya dalam **{menit:02d}:{detik:02d}**...")
        time.sleep(1)
    st.rerun()
else:
    if st.button("🚀 Mulai Screening Sekarang", type="primary", use_container_width=True):
        tampilkan_hasil()
