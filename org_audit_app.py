import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import os
import openai

st.set_page_config(page_title="Org Audit Tool", layout="wide")

st.title("Organizational Structure Audit Tool")

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

uploaded_file = st.file_uploader("Upload your org Excel file", type=["xlsx"])

def generate_recommendations(df):
    num_employees = len(df)
    num_departments = df['Department'].nunique()
    avg_span_of_control = df.groupby('Reports To').size().mean()

    prompt = f"""
    You are a management consultant analyzing an organization's structure.
    The organization has {num_employees} employees across {num_departments} departments.
    The average span of control (number of direct reports per manager) is {avg_span_of_control:.2f}.

    Based on this information, provide 3 to 5 clear recommendations for potential overhead reduction
    and organizational restructuring to improve efficiency. Focus on management layers,
    spans of control, and reducing complexity.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert organizational consultant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error communicating with OpenAI API: {e}"

def plot_network_graph(df):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_node(row['Employee ID'], label=row['Name'], title=f"{row['Role']} ({row['Department']})", level=row['Level'])
        if pd.notna(row['Reports To']):
            G.add_edge(row['Reports To'], row['Employee ID'])

    net = Network(height='750px', width='100%', directed=True)
    net.from_nx(G)

    tmp_dir = tempfile.gettempdir()
    path = os.path.join(tmp_dir, "network.html")
    net.save_graph(path)
    st.components.v1.html(open(path, 'r', encoding='utf-8').read(), height=750)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    required_cols = {'Employee ID', 'Name', 'Role', 'Department', 'Reports To', 'Level', 'Cost'}
    if not required_cols.issubset(df.columns):
        st.error(f"Excel file must contain columns: {', '.join(required_cols)}")
    else:
        st.success("File loaded successfully!")
        plot_network_graph(df)

        if st.button("Generate AI Recommendations"):
            with st.spinner("Analyzing organization..."):
                recommendations = generate_recommendations(df)
            st.subheader("AI-generated Recommendations")
            st.write(recommendations)

