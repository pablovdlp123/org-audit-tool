import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import plotly.express as px
import tempfile
import os

st.set_page_config(page_title="Org Audit Tool", layout="wide")

st.title("Organizational Structure Audit Tool")

# Upload Excel file
uploaded_file = st.file_uploader("Upload your org Excel file", type=["xlsx"])

if uploaded_file:
    # Load Excel into DataFrame
    df = pd.read_excel(uploaded_file)

    # Check required columns
    required_cols = {'Employee ID', 'Name', 'Role', 'Department', 'Reports To', 'Level', 'Cost'}
    if not required_cols.issubset(df.columns):
        st.error(f"Excel file must contain columns: {', '.join(required_cols)}")
    else:
        st.success("File loaded successfully!")

        def plot_network_graph(df):
            # Build NetworkX graph from DataFrame
            G = nx.DiGraph()
            for _, row in df.iterrows():
                G.add_node(row['Employee ID'], label=row['Name'], title=f"{row['Role']} ({row['Department']})", level=row['Level'])
                if pd.notna(row['Reports To']):
                    G.add_edge(row['Reports To'], row['Employee ID'])

            # Use PyVis to visualize
            net = Network(height='750px', width='100%', directed=True)
            net.from_nx(G)

            # Save and display in Streamlit
            tmp_dir = tempfile.gettempdir()
            path = os.path.join(tmp_dir, "network.html")
            net.save_graph(path)
            st.components.v1.html(open(path, 'r', encoding='utf-8').read(), height=750)

        def plot_org_treemap(df):
            fig = px.treemap(
                df,
                path=['Department', 'Role', 'Name'],
                values='Cost',
                color='Level',
                color_continuous_scale='Viridis',
                hover_data={'Cost': True, 'Level': True}
            )
            fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            st.plotly_chart(fig, use_container_width=True)

        visualization_type = st.selectbox(
            "Choose organization chart style",
            ["Network Graph", "Hierarchical Treemap"]
        )

        if visualization_type == "Network Graph":
            plot_network_graph(df)
        else:
            plot_org_treemap(df)
