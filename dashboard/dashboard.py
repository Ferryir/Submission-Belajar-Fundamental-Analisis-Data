import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
from pathlib import Path

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(
    page_title="E-Commerce Dashboard",
    page_icon="🛒",
    layout="wide"
)

# ==============================
# LOAD DATA
# ==============================
# Path relatif terhadap lokasi file ini (agar bisa jalan di local & Streamlit Cloud)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(SCRIPT_DIR, "main_data.csv"))
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
    return df

all_data = load_data()

# ==============================
# SIDEBAR FILTER
# ==============================
st.sidebar.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=80)
st.sidebar.title(" E-Commerce Dashboard")
st.sidebar.markdown("---")

# Date filter
min_date = all_data['order_purchase_timestamp'].min().date()
max_date = all_data['order_purchase_timestamp'].max().date()

start_date = st.sidebar.date_input("Tanggal Mulai", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Tanggal Akhir", max_date, min_value=min_date, max_value=max_date)

# Filter data
filtered = all_data[
    (all_data['order_purchase_timestamp'].dt.date >= start_date) &
    (all_data['order_purchase_timestamp'].dt.date <= end_date)
]

st.sidebar.markdown("---")
st.sidebar.markdown(f" **{filtered['order_id'].nunique():,}** orders")
st.sidebar.markdown(f" **{filtered['customer_unique_id'].nunique():,}** customers")

# ==============================
# HEADER
# ==============================
st.title(" E-Commerce Public Dataset Dashboard")
st.markdown("Dashboard interaktif untuk analisis data E-Commerce di Brasil")
st.markdown("---")

# ==============================
# KEY METRICS
# ==============================
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_orders = filtered['order_id'].nunique()
    st.metric("Total Orders", f"{total_orders:,}")

with col2:
    total_revenue = filtered['revenue'].sum()
    st.metric("Total Revenue", f"R$ {total_revenue:,.0f}")

with col3:
    avg_review = filtered['review_score'].mean()
    st.metric("Avg Review Score", f"{avg_review:.2f} ⭐")

with col4:
    avg_delivery = filtered['delivery_time'].mean()
    st.metric("Avg Delivery Time", f"{avg_delivery:.1f} hari")

st.markdown("---")

# ==============================
# CHART 1: TREN BULANAN
# ==============================
st.subheader(" Tren Order & Revenue Bulanan")

monthly = filtered.copy()
monthly['month'] = monthly['order_purchase_timestamp'].dt.to_period('M').astype(str)
monthly_agg = monthly.groupby('month').agg(
    total_orders=('order_id', 'nunique'),
    total_revenue=('revenue', 'sum')
).reset_index()

fig, ax1 = plt.subplots(figsize=(14, 5))

color_orders = '#2196F3'
color_revenue = '#FF9800'

ax1.bar(monthly_agg['month'], monthly_agg['total_orders'],
        color=color_orders, alpha=0.7, label='Jumlah Order')
ax1.set_xlabel('Bulan', fontsize=11)
ax1.set_ylabel('Jumlah Order', color=color_orders, fontsize=11)
ax1.tick_params(axis='y', labelcolor=color_orders)
ax1.tick_params(axis='x', rotation=45)

ax2 = ax1.twinx()
ax2.plot(monthly_agg['month'], monthly_agg['total_revenue'],
         color=color_revenue, linewidth=2.5, marker='o', markersize=5, label='Revenue (R$)')
ax2.set_ylabel('Revenue (R$)', color=color_revenue, fontsize=11)
ax2.tick_params(axis='y', labelcolor=color_revenue)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Tren Jumlah Order dan Revenue per Bulan', fontsize=14, fontweight='bold')
fig.tight_layout()
st.pyplot(fig)

# ==============================
# CHART 2: TOP KATEGORI PRODUK
# ==============================
st.markdown("---")
st.subheader(" Top 10 Kategori Produk")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Berdasarkan Jumlah Order**")
    top_cat_orders = filtered.groupby('product_category')['order_id'].nunique().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#2196F3' if i == 0 else '#90CAF9' for i in range(len(top_cat_orders))]
    ax.barh(top_cat_orders.index[::-1], top_cat_orders.values[::-1], color=colors[::-1])
    ax.set_xlabel('Jumlah Order')
    ax.set_title('Top 10 Kategori (Order)', fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.markdown("**Berdasarkan Revenue**")
    top_cat_rev = filtered.groupby('product_category')['revenue'].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#FF9800' if i == 0 else '#FFE0B2' for i in range(len(top_cat_rev))]
    ax.barh(top_cat_rev.index[::-1], top_cat_rev.values[::-1], color=colors[::-1])
    ax.set_xlabel('Revenue (R$)')
    ax.set_title('Top 10 Kategori (Revenue)', fontweight='bold')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))
    plt.tight_layout()
    st.pyplot(fig)

# ==============================
# CHART 3: REVIEW SCORE & DELIVERY TIME
# ==============================
st.markdown("---")
st.subheader(" Review Score & Waktu Pengiriman")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Distribusi Review Score**")
    review_counts = filtered.groupby('review_score')['order_id'].nunique()
    colors_review = ['#f44336', '#FF9800', '#FFC107', '#8BC34A', '#4CAF50']

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(review_counts.index, review_counts.values, color=colors_review, width=0.6)
    ax.set_xlabel('Review Score')
    ax.set_ylabel('Jumlah Order')
    ax.set_title('Distribusi Review Score', fontweight='bold')
    ax.set_xticks([1, 2, 3, 4, 5])
    for i, (score, val) in enumerate(review_counts.items()):
        ax.text(score, val + 100, f'{val:,}', ha='center', fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.markdown("**Rata-rata Delivery Time per Review Score**")
    delivery_review = filtered.dropna(subset=['delivery_time', 'review_score'])
    dr_grouped = delivery_review.groupby('review_score')['delivery_time'].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(dr_grouped.index, dr_grouped.values, color=colors_review, width=0.6)
    ax.set_xlabel('Review Score')
    ax.set_ylabel('Rata-rata Delivery Time (Hari)')
    ax.set_title('Delivery Time vs Review Score', fontweight='bold')
    ax.set_xticks([1, 2, 3, 4, 5])
    for score, val in dr_grouped.items():
        ax.text(score, val + 0.3, f'{val:.1f}', ha='center', fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)

# ==============================
# CHART 4: RFM ANALYSIS
# ==============================
st.markdown("---")
st.subheader(" RFM Analysis - Segmentasi Pelanggan")

reference_date = filtered['order_purchase_timestamp'].max() + pd.Timedelta(days=1)

rfm = filtered.groupby('customer_unique_id').agg(
    recency=('order_purchase_timestamp', lambda x: (reference_date - x.max()).days),
    frequency=('order_id', 'nunique'),
    monetary=('revenue', 'sum')
).reset_index()

rfm['r_score'] = pd.qcut(rfm['recency'], q=4, labels=[4, 3, 2, 1])
rfm['f_score'] = rfm['frequency'].apply(lambda x: 4 if x > 3 else (3 if x > 2 else (2 if x > 1 else 1)))
rfm['m_score'] = pd.qcut(rfm['monetary'], q=4, labels=[1, 2, 3, 4], duplicates='drop')

def rfm_segment(row):
    r = int(row['r_score'])
    f = int(row['f_score'])
    if r >= 3 and f >= 3:
        return 'Champions'
    elif r >= 3 and f >= 2:
        return 'Loyal Customers'
    elif r >= 3:
        return 'Potential Loyalists'
    elif r >= 2 and f >= 2:
        return 'At Risk'
    elif r >= 2:
        return 'Need Attention'
    else:
        return 'Lost Customers'

rfm['segment'] = rfm.apply(rfm_segment, axis=1)

# RFM Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Recency", f"{rfm['recency'].mean():.0f} hari")
with col2:
    st.metric("Avg Frequency", f"{rfm['frequency'].mean():.2f}")
with col3:
    st.metric("Avg Monetary", f"R$ {rfm['monetary'].mean():,.0f}")

# Segment chart
segment_order = ['Champions', 'Loyal Customers', 'Potential Loyalists', 'Need Attention', 'At Risk', 'Lost Customers']
segment_colors = ['#4CAF50', '#8BC34A', '#CDDC39', '#FFC107', '#FF9800', '#f44336']
segment_data = rfm['segment'].value_counts().reindex(segment_order).dropna()

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(segment_data.index[::-1], segment_data.values[::-1],
        color=[segment_colors[segment_order.index(s)] for s in segment_data.index[::-1]])
ax.set_title('Distribusi Segmen Pelanggan (RFM)', fontsize=14, fontweight='bold')
ax.set_xlabel('Jumlah Pelanggan')
for i, (seg, val) in enumerate(zip(segment_data.index[::-1], segment_data.values[::-1])):
    ax.text(val + 50, i, f'{val:,} ({val/len(rfm)*100:.1f}%)', va='center', fontsize=10)
plt.tight_layout()
st.pyplot(fig)

# ==============================
# CHART 5: GEOSPATIAL - TOP STATES
# ==============================
st.markdown("---")
st.subheader(" Distribusi Geografis Pelanggan")

customer_geo = filtered.groupby('customer_state').agg(
    total_customers=('customer_unique_id', 'nunique'),
    total_revenue=('revenue', 'sum')
).sort_values('total_customers', ascending=False).head(10).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

colors_state = ['#1565C0' if i == 0 else '#42A5F5' if i < 3 else '#90CAF9' for i in range(len(customer_geo))]

ax1.barh(customer_geo['customer_state'][::-1], customer_geo['total_customers'][::-1],
         color=colors_state[::-1])
ax1.set_title('Top 10 State - Pelanggan', fontweight='bold', fontsize=13)
ax1.set_xlabel('Jumlah Pelanggan')
for bar, val in zip(ax1.patches, customer_geo['total_customers'][::-1]):
    ax1.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
             f'{val:,}', va='center', fontsize=10)

ax2.barh(customer_geo['customer_state'][::-1], customer_geo['total_revenue'][::-1],
         color=colors_state[::-1])
ax2.set_title('Top 10 State - Revenue', fontweight='bold', fontsize=13)
ax2.set_xlabel('Revenue (R$)')
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'R$ {x/1e6:.1f}M'))

plt.suptitle('Distribusi Geografis Pelanggan', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
st.pyplot(fig)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption("© 2024 E-Commerce Dashboard | Data: Brazilian E-Commerce Public Dataset")
