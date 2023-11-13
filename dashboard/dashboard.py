import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='darkgrid')
from datetime import timedelta
import os

def create_monthly_orders_df(df):

    monthly_orders_df = all_df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "nunique",
        "payment_value": "sum",
    })

    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_approved_at": "order_month",
        "order_id": "order_count",
        "payment_value": "payment"
    }, inplace=True)

    # Explicitly specify the date format in the to_datetime function
    monthly_orders_df['order_month'] = pd.to_datetime(monthly_orders_df['order_month'], format='%b-%Y')

    # Filter rows based on the condition
    recent_month = monthly_orders_df['order_month'].max().replace(day=1)
    monthly_orders_df = monthly_orders_df[monthly_orders_df['order_month'] < recent_month]

    monthly_orders_df = monthly_orders_df.sort_values('order_month')
    return monthly_orders_df


def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name").order_id.nunique().sort_values(ascending=False).reset_index()
    return sum_order_items_df


def create_byscore_df(df):
    byscore_df = df.groupby(by="review_score").order_id.nunique().reset_index()
    byscore_df.rename(columns={
        "order_id": "order_count"
    }, inplace=True)
    
    total_orders = byscore_df['order_count'].sum()
    byscore_df['percentage'] = (byscore_df['order_count'] / total_orders) * 100

    byscore_df = byscore_df.sort_values(by='percentage', ascending=False)

    return byscore_df


def create_rfm_df(df):

    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_approved_at": "max",
        "order_id": "nunique",
        "payment_value": "sum"
    })
    
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_approved_at"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

print("Current working directory:", os.getcwd())

script_directory = os.path.dirname(os.path.abspath(__file__))
all_path = os.path.join(script_directory, "../data/all_data.csv")

all_df = pd.read_csv(all_path)

datetime_columns = ["order_approved_at"]
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])


min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()
    
with st.sidebar:

    st.image(os.path.join(script_directory, "./happy_mart.png"))
    
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value = min_date,
        max_value = max_date,
        value=[min_date, max_date]
    )


main_df = all_df[(all_df["order_approved_at"] >= str(start_date - timedelta(days=1))) & 
                (all_df["order_approved_at"] <= str(end_date + timedelta(days=1)))]

main_df.to_csv("main_data.csv", index=False)

monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
byscore_df = create_byscore_df(main_df)
rfm_df = create_rfm_df(main_df)


st.header('Happy Mart Dashboard :sparkles:')


st.subheader('Monthly Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_payment = format_currency(monthly_orders_df.payment.sum(), "BRL", locale='pt_BR') 
    st.metric("Total Payment", value=total_payment)
 
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_df["order_month"].dt.strftime('%b %Y'),
    monthly_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#0071D3"
)

ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15, rotation=45)
 
st.pyplot(fig)


st.subheader("Best & Worst Performing Categories")
    
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
    
colors = ["#0071D3", "#61BEFF", "#6AC8FF", "#74D1FF", "#7EDBFF"]
    
sns.barplot(x="order_id", y="product_category_name", data=sum_order_items_df.head(5), palette=colors, hue="product_category_name", ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Categories", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)
 
sns.barplot(x="order_id", y="product_category_name", data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette=colors, hue="product_category_name", ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Categories", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
    
st.pyplot(fig)


st.subheader("Customers Experience Score")

labels = byscore_df['review_score']
sizes = byscore_df['percentage']

fig, ax = plt.subplots(figsize=(10, 10))
colors =  ["#0071D3", "#61BEFF", "#6AC8FF", "#74D1FF", "#7EDBFF"]
ax.pie(sizes, labels=None, colors=colors, autopct='', startangle=90, wedgeprops={'linewidth': 0})

legend=ax.legend([f"{label:.0f} stars: {size:.1f}%" for label, size in zip(labels, sizes)], loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), title="Score Percentages")
for text in legend.get_texts():
    text.set_fontsize(12)

ax.axis('equal')

st.pyplot(fig)


st.subheader("Best Customer Based on RFM Parameters")
    
col1, col2, col3 = st.columns(3)
    
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
    
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
    
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR') 
    st.metric("Average Monetary", value=avg_frequency)
    
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors =  ["#0071D3", "#61BEFF", "#6AC8FF", "#74D1FF", "#7EDBFF"]
    
sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_unique_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35, rotation=45)
    
sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_unique_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35, rotation=45)
    
sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, hue="customer_unique_id", ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_unique_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35, rotation=45)
    
st.pyplot(fig)
    