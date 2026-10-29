import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import google.generativeai as genai

GEMINI_API_KEY = ""
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-3-flash-preview')

def checker(query, checklist) -> bool:
    for check in checklist:
        if check in query:
            return True
    return False

st.set_page_config(page_title="Sales Chatbot", layout="wide")
st.title("Sales Chatbot")

with st.sidebar:
    st.header("Upload CSV")
    uploaded_file = st.file_uploader("Upload sales CSV", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV file loaded succesfully")
    st.subheader("Dataframe Info")
    st.dataframe(df.head())
    all_cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    st.sidebar.subheader("Quick Analysis")
    analysis_col = st.sidebar.selectbox("Column", all_cols, index=None, placeholder="Select a column")
    if analysis_col:
        target_cols = numeric_cols if (analysis_col in categorical_cols) else []
        if analysis_col in target_cols: target_cols.remove(analysis_col)
        target_col = st.sidebar.selectbox("Target Column", target_cols, index=None, placeholder="Select target column (optional):")
        query_1_num = [
            f"Show highest {analysis_col}",
            f"Show trend of {analysis_col}",
            f"Show average {analysis_col}",
        ] if (analysis_col in numeric_cols) else []

        query_1_cat = [
            f"Show {analysis_col} distribution" if df[analysis_col].nunique() <= 20 else None,
        ] if (analysis_col in categorical_cols) else []

        query_2_cols = [
            f"Show highest {target_col} grouped by {analysis_col}",
            f"Show average {target_col} grouped by {analysis_col}",
        ] if target_col else []

        all_queries = []
        all_queries.extend(query_1_num)
        all_queries.extend(query_1_cat)
        all_queries.extend(query_2_cols)

        dropdown_question = st.sidebar.selectbox("Select a query", all_queries, index=None, placeholder="Select a query")
    else: target_col, dropdown_question = None, None

    prompt_question = st.text_input("Or manually enter your query: ", placeholder="Type your query here...")
    
    if st.button("Run", type="primary", width="stretch"):
        done = False
        if prompt_question:
            response = model.generate_content("Write python code to process the given prompt and display any relevant results using streamlit. "\
            f"The dataframe is stored in variable 'df'. The column names are: {all_cols}"\
            f"Prompt: {prompt_question}"\
            "Write only the required python code and nothing else")
            code = response.text
            code = re.sub(r"^```python\s*", "", code.strip())
            code = re.sub(r"\s*```$", "", code)
            exec_globals = {
                "df": df,
                "st": __import__("streamlit"),
                "pd": __import__("pandas"),
            }
            try:
                exec(code, exec_globals, {})
                done = True
            except Exception as e:
                st.error("Error while running AI code. Check console for more info")
                print(e)
                pattern = r"|".join(re.escape(col) for col in all_cols)
                match = re.findall(pattern, prompt_question)
                if match:
                    if len(match) == 1: analysis_col = match[0]
                    elif len(match) == 2:
                        target_col = match[0]
                        analysis_col = match[1]
                    else:
                        analysis_col = None
                        target_col = None
                else:
                    st.error("Could not understand query")

        question = prompt_question or dropdown_question
        if done: pass
        elif question and analysis_col: 
            st.subheader(question)
            q = question.lower()

            if checker(q, ["highest","max"]):
                if target_col:
                    top = df.groupby(analysis_col)[target_col].sum().idxmax()
                    st.write(f"{analysis_col} with highest {target_col}: {top}")
                    fig,ax = plt.subplots()
                    df.groupby(analysis_col)[target_col].sum().plot(kind='bar', ax=ax)
                    ax.set_ylabel(analysis_col)
                    st.pyplot(fig)
                else:
                    hig = df[analysis_col].idxmax()
                    st.write(f"{analysis_col} highest value: {hig}")

            elif checker(q, ["trend","growth"]):
                fig, ax = plt.subplots()
                ax.plot(df[analysis_col])
                ax.set_ylabel(analysis_col)
                ax.set_xlabel("Index")
                st.pyplot(fig)

            elif checker(q,["distribution"]):
                fig,ax = plt.subplots()
                data = df[analysis_col].value_counts()
                ax.pie(data, labels=data.index, autopct="%0.1f%%")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)

            elif checker(q, ["average", "avg", "mean"]):
                if target_col:
                    avg = df.groupby(analysis_col)[target_col].mean()
                    st.write(avg)
                    fig,ax = plt.subplots()
                    avg.plot(kind='bar', ax=ax)
                    ax.set_ylabel(f"Average {target_col}")
                    st.pyplot(fig)
                else:
                    avg = df[analysis_col].mean()
                    st.write(f"Average {analysis_col} = {avg}")

            else: st.error("Unknown query")
        elif not analysis_col:  st.info("No query provided")
        else: st.error("Could not understand query")
else: st.info("Upload a CSV file to get started")