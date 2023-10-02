import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import pinotdb


def get_funnel_figure(df):
    trace = go.Funnel(
        x=df.agg('sum', numeric_only=1).values,
        y=['home', 'login', 'cart', 'shop', 'help', 'error', 'checkout', 'OLD_CHECKOUT']
    )

    layout = go.Layout(margin={"l": 180, "r": 0, "t": 30, "b": 0, "pad": 0},
                       funnelmode="stack",
                       showlegend=False,
                       hovermode='closest',
                       title='',
                       legend=dict(orientation="v",
                                   bgcolor='#E2E2E2',
                                   xanchor='left',
                                   font=dict(size=12)))
    fig = go.Figure(trace, layout)
    fig.update_layout(title_text="Funnel", font_size=10)
    return fig


def get_sankey_figure(df):
    # Process the data to capture transitions
    all_transitions = []

    for path in df['web_page']:
        steps = path.split(',')
        transitions = list(zip(steps[:-1], steps[1:]))
        all_transitions.extend(transitions)

    transition_df = pd.DataFrame(all_transitions, columns=['source', 'target'])
    trans_count = (transition_df.groupby(['source', 'target'])
                   .size()
                   .reset_index(name='value')
                   .sort_values('value', ascending=False))

    # Create unique labels for the nodes
    unique_labels = pd.concat([trans_count['source'],
                               trans_count['target']]).unique()

    # Map the source and target strings to numeric values
    trans_count['source'] = trans_count['source'].map(
        {label: idx for idx, label in enumerate(unique_labels)})
    trans_count['target'] = trans_count['target'].map(
        {label: idx for idx, label in enumerate(unique_labels)})

    # Create the Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=15,
                  line=dict(color="black", width=0.5),
                  label=unique_labels),
        link=dict(arrowlen=15,
                  source=trans_count['source'],
                  target=trans_count['target'],
                  value=trans_count['value'])
    ))

    fig.update_layout(title_text="User Flow", font_size=10)
    return fig


def get_connection():
    conn = pinotdb.connect(host='localhost', port=9000,
                           path='/sql', scheme='http')
    return conn


def get_funnel_data(conn):
    query = """SELECT
                SUM(case when web_page='home' then 1 else 0 end) as home,
                SUM(case when web_page='login' then 1 else 0 end) as login,
                SUM(case when web_page='cart' then 1 else 0 end) as cart,
                SUM(case when web_page='shop' then 1 else 0 end) as shop,
                SUM(case when web_page='help' then 1 else 0 end) as help,
                SUM(case when web_page='error' then 1 else 0 end) as error,
                SUM(case when web_page='checkout' then 1 else 0 end) as checkout,
                SUM(case when web_page='OLD_CHECKOUT' then 1 else 0 end) as OLD_CHECKOUT,
                location,
                user_id
                FROM clickstream
                GROUP BY location, user_id
                LIMIT 200
            """
    df = pd.read_sql_query(query, conn)
    return df


def get_sankey_data(conn):
    df = pd.read_sql_query('SELECT * FROM clickstream LIMIT 200', conn)
    df = df.groupby(['location', 'user_id'])['web_page'].apply(lambda x: ','.join(x)).reset_index()
    return df


conn = get_connection()

# update every 30 seconds
st_autorefresh(interval=30 * 1000, key="dataframerefresh")

# Funnel Chart
funnel_data = get_funnel_data(conn)
funnel_fig = get_funnel_figure(funnel_data)
st.plotly_chart(funnel_fig, use_container_width=True)

# Sankey Chart
sankey_data = get_sankey_data(conn)
sankey_fig = get_sankey_figure(sankey_data)
st.plotly_chart(sankey_fig, use_container_width=True)