import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import speech_recognition as sr

# --- Page setup ---
st.set_page_config(page_title="Offline Sales Chatbot", layout="wide")
st.title("📊 Offline Sales Chatbot with Charts & Voice & Prompt")

# --- Sidebar ---
with st.sidebar:
    st.header("Upload CSV")
    uploaded_file = st.file_uploader("Upload your sales CSV", type=['csv'])

    st.header("Voice Input")
    use_voice = st.checkbox("Use offline voice input")

# --- Load Data ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV loaded successfully!")
    st.dataframe(df.head())

    # Detect numeric & categorical columns
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    st.sidebar.subheader("Select Column for Analysis")
    analysis_col = st.sidebar.selectbox("Column", numeric_cols + categorical_cols)

    # --- Voice Input ---
    user_question = ""
    if use_voice:
        st.info("Press 'Record' and speak your question about sales data.")
        if st.button("Record"):
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.write("Listening...")
                audio = r.listen(source)
            try:
                user_question = r.recognize_google(audio)
                st.write(f"You said: {user_question}")
            except sr.UnknownValueError:
                st.error("Could not understand audio")
            except sr.RequestError:
                st.error("Speech recognition error")

    # --- Dropdown Questions ---
    st.sidebar.subheader("Predefined Questions")
    dropdown_question = st.sidebar.selectbox("Choose a question",
                                             ["Which category/state had the highest sales?",
                                              "Show sales trend",
                                              "Show average sales by category"])

    # --- Text Prompt ---
    prompt_question = st.text_input("Or type your question here:")

    # --- Combine questions ---
    final_question = user_question or prompt_question or dropdown_question

    if st.button("Get Answer"):
        st.subheader(f"Answer for: {final_question}")

        q = final_question.lower()

        if "highest" in q and categorical_cols and numeric_cols:
            col_num = numeric_cols[0]
            col_cat = categorical_cols[0]
            top = df.groupby(col_cat)[col_num].sum().idxmax()
            st.write(f"✅ {col_cat} with highest {col_num}: {top}")
            fig, ax = plt.subplots()
            df.groupby(col_cat)[col_num].sum().plot(kind='bar', ax=ax)
            ax.set_ylabel(col_num)
            st.pyplot(fig)

        elif "trend" in q and numeric_cols:
            col_num = numeric_cols[0]
            fig, ax = plt.subplots()
            df[col_num].plot(kind='line', ax=ax)
            ax.set_ylabel(col_num)
            ax.set_xlabel("Index")
            st.pyplot(fig)

        elif "average" in q and categorical_cols and numeric_cols:
            col_num = numeric_cols[0]
            col_cat = categorical_cols[0]
            avg_df = df.groupby(col_cat)[col_num].mean()
            st.write(avg_df)
            fig, ax = plt.subplots()
            avg_df.plot(kind='bar', ax=ax)
            ax.set_ylabel(f"Average {col_num}")
            st.pyplot(fig)

        else:
            st.info("❌ Could not understand the question. Try using predefined questions or keywords like 'highest', 'trend', 'average'.")

else:
    st.info("Upload a CSV file to get started.")
