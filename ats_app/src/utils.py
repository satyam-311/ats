import PyPDF2 as pdf
import plotly.graph_objects as go
import streamlit as st

def extract_text_from_pdf(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return None

def create_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Match Score"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#4f46e5"}}
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    return fig
