import os
import pandas as pd
import numpy as np

INPUT_FILE = r'C:\Study\Hoctap\OLAP\spotify_2025.csv'
OUTPUT_FILE = r'C:\Study\Hoctap\OLAP\Spotify_2025_cleaned_data.csv'

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# --- 1. Đọc dữ liệu ---
df = pd.read_csv(INPUT_FILE, encoding='utf-8')

df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
df['album_release_date'] = pd.to_datetime(df['album_release_date'], errors='coerce')

df_clean = df[df['snapshot_date'].dt.year == 2025].copy()
df_clean.dropna(subset=['snapshot_date'], inplace=True)

# --- 2. Chuẩn hoá các cột float ---
float_cols = [
    'energy','danceability','acousticness','valence','instrumentalness',
    'tempo','loudness','speechiness','liveness'
]

for col in float_cols:
    df_clean[col] = (
        pd.to_numeric(df_clean[col], errors='coerce')
        .fillna(0.0)
        .astype(float)
    )

# --- 3. Chuẩn hoá các cột integer ---
int_cols = [
    'daily_rank','daily_movement','weekly_movement','popularity',
    'duration_ms','key','mode','time_signature'
]

for col in int_cols:
    df_clean[col] = (
        pd.to_numeric(df_clean[col], errors='coerce')
        .fillna(0)
        .astype(np.int32)
    )

# --- 4. Chuẩn hóa COUNTRY ---
df_clean['country_clean'] = (
    df_clean['country']
      .fillna('GLOBAL')
      .astype(str)
      .str.strip()
      .str.upper()
)
df_clean.loc[df_clean['country_clean'] == '', 'country_clean'] = 'GLOBAL'

# --- 5. Chuẩn hóa is_explicit ---
df_clean['is_explicit_clean'] = (
    df_clean['is_explicit']
      .astype(str).str.upper()
      .map({'TRUE': 1, 'FALSE': 0})
      .fillna(0)
      .astype(np.int32)
)

# --- 6. duration_min ---
df_clean['duration_min'] = df_clean['duration_ms'] / 60000.0

# --- 7. DIM DATE ---
df_clean['date_key'] = df_clean['snapshot_date'].dt.strftime('%Y%m%d').astype(np.int32)
df_clean['year'] = df_clean['snapshot_date'].dt.year.astype(np.int32)
df_clean['month'] = df_clean['snapshot_date'].dt.month.astype(np.int32)
df_clean['day'] = df_clean['snapshot_date'].dt.day.astype(np.int32)
df_clean['quarter'] = df_clean['snapshot_date'].dt.quarter.astype(np.int32)
df_clean['day_of_week'] = df_clean['snapshot_date'].dt.dayofweek.apply(lambda x: (x + 1) % 7 + 1)
df_clean['is_weekend'] = df_clean['snapshot_date'].dt.dayofweek.isin([5, 6]).astype(np.int32)

# --- 8. genre_proxy ---
energy_high = df_clean['energy'] > 0.7
danceability_high = df_clean['danceability'] > 0.7
acousticness_high = df_clean['acousticness'] > 0.6
valence_low = df_clean['valence'] < 0.3
instrumentalness_high = df_clean['instrumentalness'] > 0.5
tempo_high = df_clean['tempo'] > 140

low_energy_conditions = [
    acousticness_high, valence_low, instrumentalness_high, tempo_high
]
low_energy_choices = [
    "Acoustic/Chill", "Sad/Low", "Instrumental", "EDM/Fast"
]

high_energy_conditions = [
    danceability_high, acousticness_high, valence_low, instrumentalness_high, tempo_high
]
high_energy_choices = [
    "Dance/Party", "Acoustic/Chill", "Sad/Low", "Instrumental", "EDM/Fast"
]

df_clean['genre_proxy'] = np.where(
    energy_high,
    np.select(high_energy_conditions, high_energy_choices, default="Pop/Mixed"),
    np.select(low_energy_conditions, low_energy_choices, default="Pop/Mixed")
)

# --- 9. Xuất file duy nhất ---
df_clean.to_csv(OUTPUT_FILE, index=False)
print("✅ Đã xuất file sạch:", OUTPUT_FILE)
