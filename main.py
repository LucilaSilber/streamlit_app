import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

background_color = '#F5F5F5'
female_color = 'orange'
female_light_color = 'wheat'
male_color = 'olive'
male_light_color = 'darkseagreen'


st.markdown(
    """
    <style>
    .main {
    background-color: #F5F5F5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

shopping_data = pd.read_csv('data/customer_shopping_data.csv')
shopping_data['price (k)'] = shopping_data.apply(lambda x: x['price']/1000, axis=1)

st.title('Which type of store would generate the maximal profit, for a mall based on historical purchases?')


malls = list(set(shopping_data['shopping_mall']))
mall_picker = st.selectbox('Which mall would you like to analyze?', options=malls, index = 0)
mall_df = shopping_data[shopping_data['shopping_mall'] == mall_picker]

st.header(f'What is the largest audience group in \'{mall_picker}\'?')
# generate the treemap chart
age_min = min(mall_df['age'])
age_max = max(mall_df['age'])
bins = range(age_min, age_max, 5)


mall_df['age_bin'] = pd.cut(mall_df['age'], bins=bins)
age_bins_str = [(str(bin_value)) for bin_value in mall_df['age_bin']]
mall_df['age_bin'] = age_bins_str
df_grouped = mall_df.groupby(['gender', 'age_bin']).size().reset_index(name='count')

fig = go.Figure()
# Add bars for each gender
for gender in df_grouped['gender'].unique():
    if gender == 'Male':
        fig.add_trace(go.Bar(
            x=df_grouped[df_grouped['gender'] == gender]['age_bin'],
            y=df_grouped[df_grouped['gender'] == gender]['count'],
            name=gender,
            marker_color=male_color
        ))
    else:
        fig.add_trace(go.Bar(
            x=df_grouped[df_grouped['gender'] == gender]['age_bin'],
            y=df_grouped[df_grouped['gender'] == gender]['count'],
            name=gender,
            marker_color=female_color
        ))

# Update layout
fig.update_layout(
    xaxis_title='Age Bins',
    yaxis_title='Count',
    margin = dict(l=5,r=5,b=10, t=10), paper_bgcolor= background_color
)
st.write(fig)
largest_subgroup = df_grouped.loc[df_grouped['count'].idxmax()]
st.text(f'The largest audience group is {largest_subgroup[0]} of age {largest_subgroup[1]}. The group size is {largest_subgroup[2]}.')

# choose audience group
gender_picker = st.selectbox('Select a Gender', options=['Male','Female'], index = 0)
age_option = sorted(list(set(age_bins_str)))
age_picker = st.selectbox('Select an Age Bin', options=age_option, index = 0)
audiance_mall = mall_df[mall_df['gender'] == gender_picker]
audiance_mall = audiance_mall[audiance_mall['age_bin'] == age_picker]
group_size = len(audiance_mall)
st.text('The chosen group is of size: ' +str(group_size))


if gender_picker == 'Female':
    graphs_color = female_color
    graph_light = female_light_color
else:
    graphs_color = male_color
    graph_light = male_light_color

# generate a categories\profit bar chart
st.header(f'What are the favorite category and the most profitable one for {gender_picker}s of age {age_picker} in \'{mall_picker}\'?')
category_profit = audiance_mall.groupby('category').agg({'price (k)': ['size', 'sum']}).reset_index()
category_profit.columns = ['Category', '# purchases', 'Total profit (k$)']

# Creating a bar chart using Plotly
fig4 = px.bar(category_profit, x='Category', y=['# purchases', 'Total profit (k$)'],
              labels={'value': 'Count'},
              barmode='group',
              color_discrete_map={'# purchases': graphs_color, 'Total profit (k$)': graph_light})
fig4.update_layout(margin = dict(l=5,r=5,b=10, t=10), paper_bgcolor= background_color,xaxis_title='Category', yaxis_title='Frequency\\Profit')
st.write(fig4)


top3 = list(category_profit.sort_values(by='# purchases',ascending=False)['Category'][:3])
profitable3 = list(category_profit.sort_values(by='Total profit (k$)',ascending=False)['Category'][:3])
st.markdown(f'**1) Top visited category:** {top3[0]}, **Most profitable:** {profitable3[0]}')
st.markdown(f'**2) Top visited category:** {top3[1]}, **Most profitable:** {profitable3[1]}')
st.markdown(f'**3) Top visited category:** {top3[2]}, **Most profitable:** {profitable3[2]}')

#generate category trendlines
st.header(f'Trendlines over time per category for {gender_picker}s of age {age_picker} in \'{mall_picker}\'')
audiance_mall['invoice_date'] = pd.to_datetime(audiance_mall['invoice_date'],format="%d/%m/%Y")
audiance_mall['month_year'] = audiance_mall['invoice_date'].dt.strftime('%Y-%m')
# Define start and end dates
min_date = audiance_mall['invoice_date'].min()
max_date = audiance_mall['invoice_date'].max()

# Select a date range
selected_range = st.date_input('Select a date range', value=(min_date, max_date),
                               min_value=min_date, max_value=max_date, key='date_range')
st.text('Make sure to choose a valid date range including at least two months.')
start_date = pd.Timestamp(selected_range[0])
end_date = pd.Timestamp(selected_range[1])

# Select categorises to include in the trendlines
category_options = list(category_profit['Category'])
selected_categories = st.multiselect('Select categories to review', category_options, default=[top3[0],top3[1]])

# Select which data to generate the trend
options = ['# Purchases', 'Profit']
selected_option = st.radio('Which trend should be displayed?', options)

audiance_mall_dated = audiance_mall[(audiance_mall['invoice_date'] >= start_date) & (audiance_mall['invoice_date'] <= end_date)]
audiance_mall_dated = audiance_mall_dated[audiance_mall_dated['category'].isin(selected_categories)]

if selected_option == '# Purchases':
    cross_tab = pd.crosstab(audiance_mall_dated['month_year'], audiance_mall_dated['category'])
    fig3 = px.line(cross_tab)
    fig3.update_xaxes(type='category')
    fig3.update_layout(xaxis_title='Month - Year', yaxis_title='# Purchases in Category',margin = dict(l=5,r=5,b=10, t=10), paper_bgcolor= background_color)

    date_range = pd.date_range(start=start_date, end=end_date, freq='QS')
    quarters_list = date_range.strftime('%Y-%m').tolist()

    date_range = pd.date_range(start=start_date, end=end_date, freq='YS')
    years_list = date_range.strftime('%Y-%m').tolist()

    for q in quarters_list:
        fig3.add_vline(x=q, line_width=1, line_dash="dash", line_color="gray")
    for y in years_list:
        fig3.add_vline(x=y, line_width=1, line_color="gray")
    st.write(fig3)

else:
    cross_tab_profit = pd.crosstab(audiance_mall_dated['month_year'], audiance_mall_dated['category'], values=audiance_mall_dated['price'], aggfunc='sum')
    cross_tab_profit = cross_tab_profit.fillna(0)
    fig5 = px.line(cross_tab_profit)
    fig5.update_xaxes(type='category')
    fig5.update_layout(xaxis_title='Month - Year', yaxis_title='Total monthly profit in Category',
                       margin=dict(l=5, r=5, b=10, t=10), paper_bgcolor=background_color)

    date_range = pd.date_range(start=start_date, end=end_date, freq='QS')
    quarters_list = date_range.strftime('%Y-%m').tolist()

    date_range = pd.date_range(start=start_date, end=end_date, freq='YS')
    years_list = date_range.strftime('%Y-%m').tolist()

    for q in quarters_list:
        fig5.add_vline(x=q, line_width=1, line_dash="dash", line_color="gray")
    for y in years_list:
        fig5.add_vline(x=y, line_width=1, line_color="gray")
    st.write(fig5)