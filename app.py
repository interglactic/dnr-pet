import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="VetCare Pro System", layout="wide", page_icon="🏥")

# --- DATABASE SIMULATION (Session State) ---
if 'db_obat' not in st.session_state:
    st.session_state.db_obat = pd.DataFrame([
        {"Nama": "Vaksin Rabies", "Stok": 50, "Harga": 150000},
        {"Nama": "Obat Cacing", "Stok": 100, "Harga": 25000}
    ])

if 'db_tindakan' not in st.session_state:
    st.session_state.db_tindakan = pd.DataFrame([
        {"Nama": "Konsultasi Umum", "Harga": 50000},
        {"Nama": "Operasi Steril", "Harga": 750000}
    ])

if 'db_pasien' not in st.session_state:
    st.session_state.db_pasien = pd.DataFrame(columns=["ID", "Pemilik", "Hewan", "Rekam Medis"])

if 'antrian' not in st.session_state:
    st.session_state.antrian = []

if 'transaksi' not in st.session_state:
    st.session_state.transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Pasien", "Tindakan", "Obat", "Total", "Kategori"])

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("NAVIGASI SISTEM", 
    ["Dashboard & Grafik", "Antrian Pasien", "Data Pasien & Rekam Medis", "Kasir (Cetak Struk)", "Stok Obat & Harga"])

# --- 1. DASHBOARD & GRAFIK ---
if menu == "Dashboard & Grafik":
    st.title("📊 Laporan & Analitik Klinik")
    
    # Filter Waktu
    df = st.session_state.transaksi
    today = datetime.now().strftime("%Y-%m-%d")
    this_month = datetime.now().strftime("%Y-%m")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pendapatan Hari Ini", f"Rp {df[df['Tanggal'] == today]['Total'].sum():,}")
    col2.metric("Pasien Hari Ini", len(df[df['Tanggal'] == today]))
    col3.metric("Obat Terjual (Bulan Ini)", len(df[(df['Bulan'] == this_month) & (df['Kategori'] == 'Obat')]))
    col4.metric("Total Tindakan (Bulan Ini)", len(df[(df['Bulan'] == this_month) & (df['Kategori'] == 'Tindakan')]))

    if not df.empty:
        st.subheader("Grafik Pendapatan")
        fig = px.pie(df, values='Total', names='Kategori', title="Proporsi Pendapatan: Tindakan vs Obat")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Data Transaksi Lengkap")
        st.dataframe(df, use_container_width=True)

# --- 2. ANTRIAN ---
elif menu == "Antrian Pasien":
    st.title("🕒 Sistem Antrian")
    with st.form("tambah_antrian"):
        nama = st.text_input("Nama Hewan / Pemilik")
        tambah = st.form_submit_button("Masukkan ke Antrian")
        if tambah:
            st.session_state.antrian.append(nama)
    
    st.subheader("Daftar Antrian Sekarang")
    for i, p in enumerate(st.session_state.antrian):
        st.write(f"{i+1}. **{p}**")
    if st.button("Panggil / Selesai"):
        if st.session_state.antrian:
            selesai = st.session_state.antrian.pop(0)
            st.success(f"Pasien {selesai} telah diproses.")

# --- 3. DATA PASIEN & REKAM MEDIS ---
elif menu == "Data Pasien & Rekam Medis":
    st.title("📂 Rekam Medis Pasien")
    with st.expander("Tambah Pasien Baru"):
        with st.form("f_pasien"):
            id_p = st.text_input("ID/No. Registrasi")
            pemilik = st.text_input("Nama Pemilik")
            hewan = st.text_input("Nama Hewan")
            rm = st.text_area("Catatan Medis Awal")
            if st.form_submit_button("Simpan"):
                new_p = pd.DataFrame([[id_p, pemilik, hewan, rm]], columns=st.session_state.db_pasien.columns)
                st.session_state.db_pasien = pd.concat([st.session_state.db_pasien, new_p], ignore_index=True)

    st.dataframe(st.session_state.db_pasien, use_container_width=True)

# --- 4. KASIR & CETAK STRUK ---
elif menu == "Kasir (Cetak Struk)":
    st.title("💸 Kasir Pembayaran")
    
    col_a, col_b = st.columns(2)
    with col_a:
        pilih_p = st.selectbox("Pilih Pasien", st.session_state.db_pasien["Hewan"] + " - " + st.session_state.db_pasien["Pemilik"])
        pilih_t = st.multiselect("Tindakan Medis", st.session_state.db_tindakan["Nama"])
        pilih_o = st.multiselect("Obat yang Diberikan", st.session_state.db_obat["Nama"])
    
    # Hitung Total
    total_t = st.session_state.db_tindakan[st.session_state.db_tindakan["Nama"].isin(pilih_t)]["Harga"].sum()
    total_o = st.session_state.db_obat[st.session_state.db_obat["Nama"].isin(pilih_o)]["Harga"].sum()
    grand_total = total_t + total_o

    with col_b:
        st.info(f"### Total Tagihan: Rp {grand_total:,}")
        if st.button("Proses & Kurangi Stok"):
            # Update Stok Otomatis
            for o in pilih_o:
                st.session_state.db_obat.loc[st.session_state.db_obat["Nama"] == o, "Stok"] -= 1
            
            # Simpan Transaksi
            now = datetime.now()
            new_trx = pd.DataFrame([
                {"Tanggal": now.strftime("%Y-%m-%d"), "Bulan": now.strftime("%Y-%m"), "Pasien": pilih_p, "Tindakan": str(pilih_t), "Obat": str(pilih_o), "Total": grand_total, "Kategori": "Campuran"}
            ])
            st.session_state.transaksi = pd.concat([st.session_state.transaksi, new_trx], ignore_index=True)
            
            # Simulasi Invoice
            st.subheader("📄 INVOICE (Siap Cetak)")
            invoice_text = f"""
            KLINIK HEWAN VETCARE
            ---------------------------
            Pasien: {pilih_p}
            Tindakan: {pilih_t}
            Obat: {pilih_o}
            ---------------------------
            TOTAL: Rp {grand_total:,}
            Terima Kasih!
            """
            st.code(invoice_text)
            st.caption("Gunakan Ctrl+P pada browser untuk mencetak ke printer struk")

# --- 5. STOK OBAT & HARGA ---
elif menu == "Stok Obat & Harga":
    st.title("💊 Inventori Obat & Tindakan")
    
    t1, t2 = st.tabs(["Data Obat", "Data Harga Tindakan"])
    with t1:
        st.dataframe(st.session_state.db_obat, use_container_width=True)
        # Fitur tambah stok bisa diletakkan di sini
    with t2:
        st.table(st.session_state.db_tindakan)
