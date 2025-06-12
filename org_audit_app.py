import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile

def run_audit(df):
    span_of_control = df['Reports To'].value_counts().rename_axis('Manager ID').reset_index(name='Direct Reports')
    span_of_control = span_of_control.merge(df[['Employee ID', 'Name']], left_on='Manager ID', right_on='Employee ID', how='left')
    span_of_control = span_of_control[['Manager ID', 'Name', 'Direct Reports']]
    low_span_managers = span_of_control[span_of_control['Direct Reports'] < 2]
    
    org_depth = df['Level'].max()
    cost_per_level = df.groupby('Level')['Cost'].sum().reset_index(name='Total Cost')
    duplicates = df.groupby(['Department', 'Role']).size().reset_index(name='Count')
    duplicate_roles = duplicates[duplicates['Count'] > 1]
    
    return {
        "span_of_control": span_of_control,
        "low_span_managers": low_span_managers,
        "org_depth": org_depth,
        "cost_per_level": cost_per_level,
        "duplicate_roles": duplicate_roles
    }

def visualize_org_chart(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        label = f"{row['Name']} ({row['Role']})"
        G.add_node(row['Employee ID'], label=label, title=f"{label}\nDept: {row['Department']}\nLocation: {row['Location']}")

    for _, row in df.iterrows():
        if pd.notna(row['Reports To']):
            G.add_edge(int(row['Reports To']), row['Employee ID'])

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)
    net.toggle_physics(True)
    net.show_buttons(filter_=['physics'])

    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
        net.save_graph(tmp_file.name)
        html_content = tmp_file.read().decode('utf-8')

    components.html(html_content, height=650, scrolling=True)

def main():
    st.title("Org Structure Audit & Visualization Tool")
    st.markdown("Upload your org chart Excel file to run audit and visualize the structure.")

    uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success("File loaded successfully!")
            st.write("### Sample of uploaded data", df.head())

            # Show org chart visualization
            st.write("## Org Chart Visualization")
            visualize_org_chart(df)

            audit_results = run_audit(df)

            st.write("## Audit Results")
            st.write("### Span of Control")
            st.dataframe(audit_results["span_of_control"])

            st.write("### Managers with Low Span (<2 direct reports)")
            st.dataframe(audit_results["low_span_managers"])

            st.write(f"### Org Depth (Max Levels): {audit_results['org_depth']}")

            st.write("### Cost per Level")
            st.dataframe(audit_results["cost_per_level"])

            st.write("### Duplicate Roles in Same Department")
            if not audit_results["duplicate_roles"].empty:
                st.dataframe(audit_results["duplicate_roles"])
            else:
                st.write("No duplicate roles found.")

            st.write("### AI Recommendations")
            st.info("GPT integration coming soon!")

        except Exception as e:
            st.error(f"Error loading file: {e}")

if __name__ == "__main__":
    main()
