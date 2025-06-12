import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
from openai import OpenAI

# <-- Insert your OpenAI API key here -->
OPENAI_API_KEY = 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

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Now use client normally:
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)

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

def generate_ai_recommendations(audit_results):
    prompt = f"""
You are an expert organizational consultant.

Given the following audit results, provide clear, concise recommendations to improve organizational structure, reduce overhead, and optimize span of control.

Audit results:
- Span of control summary: {audit_results['span_of_control'].to_dict(orient='records')}
- Managers with low span (<2): {audit_results['low_span_managers'].to_dict(orient='records')}
- Org depth (max levels): {audit_results['org_depth']}
- Cost per level: {audit_results['cost_per_level'].to_dict(orient='records')}
- Duplicate roles in same department: {audit_results['duplicate_roles'].to_dict(orient='records')}

Please provide 3 to 5 actionable recommendations.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def main():
    st.title("Org Structure Audit & Visualization Tool with AI Recommendations")
    st.markdown("Upload your org chart Excel file to run audit, visualize, and get AI-driven recommendations.")

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

            st.write("## AI Recommendations")
            recommendations = generate_ai_recommendations(audit_results)
            st.info(recommendations)

        except Exception as e:
            st.error(f"Error loading file: {e}")

if __name__ == "__main__":
    main()
