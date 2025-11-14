# app.py
# This is the main Streamlit application file. It manages the UI,
# navigation, and calls the helper functions from utils.py to handle API logic.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, List, Any

# Import helper functions from the local utils.py file
from utils import call_groq_api, call_pollination_ai_api, get_groq_response_text

# --- Streamlit App Initialization ---
st.set_page_config(page_title="Pro AI Assistant 💡", layout="wide")
st.title("Pro AI Assistant 💡")

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Chat", "Data Analysis", "Image Generation", "Roadmaps"])

# --- Page Logic ---

if page == "Chat":
    st.header("💬 Smart Chat")
    st.write("Hello! I'm here to help you with your academic and career goals. What would you like to achieve?")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm here to help you with your academic and career goals. What would you like to achieve?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        chat_history_for_api = [
            {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        with st.spinner("Thinking..."):
            response = call_groq_api(chat_history_for_api)
            if response:
                assistant_response = get_groq_response_text(response)
                with st.chat_message("assistant"):
                    st.write(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})


elif page == "Data Analysis":
    st.header("📊 Data Analysis")
    st.write("Upload a CSV, Excel, or JSON file, and I'll provide a detailed analysis.")

    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])

    if uploaded_file:
        file_type = uploaded_file.type
        df = None

        try:
            if "csv" in file_type:
                df = pd.read_csv(uploaded_file)
            elif "excel" in file_type:
                df = pd.read_excel(uploaded_file)
            elif "json" in file_type:
                df = pd.read_json(uploaded_file)
            else:
                st.error("Unsupported file type.")
                st.stop()

            st.write("### Data Preview")
            st.dataframe(df.head())

            st.write("### Summary Statistics")
            st.dataframe(df.describe())

            # Data Cleaning
            st.write("### Data Cleaning")
            num_duplicates = df.duplicated().sum()
            st.write(f"Found {num_duplicates} duplicate rows.")
            df.drop_duplicates(inplace=True)

            num_missing = df.isnull().sum().sum()
            st.write(f"Found {num_missing} missing values.")
            
            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    df[column].fillna(df[column].mean(), inplace=True)
                else:
                    df[column].fillna(df[column].mode()[0], inplace=True)
            
            st.success("Data cleaning completed.")

            st.write("### Key Insights & Visualizations")
            
            columns = ", ".join(df.columns)
            insight_prompt = f"Given a dataset with the following columns: {columns}. What are some potential key insights we could get from this data? Be concise and professional."
            
            with st.spinner("Generating insights..."):
                insight_response = call_groq_api([{"role": "user", "content": insight_prompt}])
                if insight_response:
                    insight_text = get_groq_response_text(insight_response)
                    st.info(insight_text)

            st.write("#### Visualizations")
            
            numerical_cols = df.select_dtypes(include=['number']).columns
            if len(numerical_cols) > 0:
                selected_col = st.selectbox("Select a numerical column for a histogram:", numerical_cols)
                if selected_col:
                    fig, ax = plt.subplots()
                    sns.histplot(df[selected_col], ax=ax)
                    ax.set_title(f"Histogram of {selected_col}")
                    st.pyplot(fig)
            else:
                st.write("No numerical columns found for a histogram.")

            if len(numerical_cols) > 1:
                st.write("##### Correlation Heatmap")
                fig, ax = plt.subplots()
                sns.heatmap(df[numerical_cols].corr(), annot=True, ax=ax, cmap="coolwarm")
                ax.set_title("Correlation Heatmap")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"An error occurred during data analysis: {e}")

elif page == "Image Generation":
    st.header("🖼️ Image Generation")
    st.write("Describe the image you want to create, and I'll generate it for you.")

    image_prompt = st.text_input("Describe the image you want to generate:", "A photorealistic cat wearing a tiny space helmet, floating in space.")
    
    if st.button("Generate Image"):
        if image_prompt:
            image_data = call_pollination_ai_api(image_prompt)
            if image_data:
                image_bytes = base64.b64decode(image_data)
                st.image(image_bytes, caption=image_prompt, use_container_width=True)
        else:
            st.warning("Please enter a description for the image.")

elif page == "Roadmaps":
    st.header("🗺️ Roadmaps & Study Plans")
    st.write("I can help you with your learning journey! Please choose a roadmap below.")

    roadmap_goal = st.selectbox("Select a learning goal:", ["Machine Learning Engineer", "Web Developer (Frontend)", "Data Scientist"])
    
    if st.button("Get Roadmap"):
        st.success(f"Here is your roadmap for a {roadmap_goal} career path!")
        st.write(f"The PDF is a placeholder, but this is where the link to a real document would go.")
        st.markdown(
            f"**[Download Roadmap PDF for {roadmap_goal}](https://example.com/placeholder-roadmap.pdf)**"
        )
        st.warning("Note: The link above is a placeholder. In a complete application, this would point to a real PDF file.")
