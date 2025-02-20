import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="Business Growth Recommender", layout="wide")

# ---------------------- FILE UPLOADER ----------------------

def load_data():
    uploaded_file = st.file_uploader("Upload your dataset (Excel format)", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        df['Growth_Category'] = (df['Age'] >= 5).astype(int)
        practice_columns = [col for col in df.columns if col not in ['Company ID', 'Age', 'Growth_Category']]
        practice_columns = [col for col in practice_columns if df[col].nunique() > 1]
        df[practice_columns] = df[practice_columns].fillna(0).astype(int)
        return df, practice_columns
    return None, None

df, practice_columns = load_data()

# ---------------------- MODEL TRAINING FUNCTION ----------------------

def train_model(df, practice_columns):
    if df is not None and practice_columns:
        X = df[practice_columns]
        y = df['Growth_Category']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        rf_model = RandomForestClassifier(n_estimators=200, random_state=42)
        rf_model.fit(X_train, y_train)
        accuracy = accuracy_score(y_test, rf_model.predict(X_test))
        feature_importance = pd.DataFrame({'Practice': X.columns, 'Importance': rf_model.feature_importances_})
        feature_importance = feature_importance.sort_values(by="Importance", ascending=False)
        return rf_model, accuracy, feature_importance
    return None, None, None

rf_model, accuracy, feature_importance = train_model(df, practice_columns)

# ---------------------- SIDEBAR NAVIGATION ----------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Model Training", "User Assessment", "Results & Recommendations"])

# ---------------------- PAGE HANDLING ----------------------
if page == "Home":
    st.title("📊 Business Growth Recommender Dashboard")
    st.write("Upload your business dataset and get personalized recommendations to enhance growth!")
    st.info("Navigate using the sidebar to train the model and assess your business practices.")
    if df is not None:
        st.success("Dataset successfully loaded! Proceed to Model Training.")

elif page == "Model Training":
    st.title("⚙️ Model Training & Evaluation")
    if df is not None:
        st.write(f"Model Accuracy: **{accuracy:.2f}%**")
        st.subheader("Feature Importance")
        fig, ax = plt.subplots()
        sns.barplot(x=feature_importance['Importance'][:10], y=feature_importance['Practice'][:10], palette='coolwarm', ax=ax)
        ax.set_xlabel("Importance Score")
        ax.set_ylabel("Business Practices")
        st.pyplot(fig)
        with open("random_forest_model.pkl", "wb") as f:
            pickle.dump(rf_model, f)
    else:
        st.warning("Please upload a dataset on the Home page.")

elif page == "User Assessment":
    st.title("📋 Business Practice Assessment")
    st.write("Answer a few questions to analyze your business growth potential.")
    if rf_model is not None:
        user_input = {}
        for practice in feature_importance['Practice'].head(10):
            user_input[practice] = st.radio(f"Are you using {practice}?", ('No', 'Yes'))
        st.session_state['user_input'] = user_input
        st.success("Responses recorded! Navigate to Results & Recommendations.")
    else:
        st.warning("Please train the model first.")

elif page == "Results & Recommendations":
    st.title("📈 Results & Recommendations")
    if rf_model is not None and 'user_input' in st.session_state:
        user_input = st.session_state['user_input']
        user_df = pd.DataFrame([{p: 1 if user_input.get(p, 'No') == 'Yes' else 0 for p in practice_columns}])
        growth_probability = rf_model.predict_proba(user_df)[0][1] * 100
        not_adapted = [practice for practice, value in user_input.items() if value == 'No']
        recommendations = feature_importance[feature_importance['Practice'].isin(not_adapted)].sort_values(by="Importance", ascending=False).head(5)['Practice'].tolist()
        st.subheader(f"Your business has a **{growth_probability:.2f}%** chance of growth.")
        if recommendations:
            st.subheader("🚀 Recommended Practices to Adopt")
            for i, rec in enumerate(recommendations, start=1):
                st.write(f"{i}. **{rec}**")
        else:
            st.success("Your business is already on a strong growth path! Keep focusing on your strengths.")
    else:
        st.warning("Please complete the User Assessment first.")
