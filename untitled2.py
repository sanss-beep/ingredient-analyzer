import time
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# 1. Website Page Setup
st.set_page_config(page_title="PureScan AI", page_icon="🔍", layout="centered")

# 2. Header & Instructions
st.title("🔍 PureScan: Food & Cosmetic Analyzer")
st.write("Upload a photo of any food or skincare ingredient list to uncover hidden toxins, allergens, chemical conflicts, and deceptive marketing!")

# 3. API Key Setup (Safe on both Streamlit Cloud and locally)
st.sidebar.header("⚙️ Project Settings")
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.sidebar.success("API Key loaded securely.")
except Exception:
    pass

if not api_key:
    api_key = st.sidebar.text_input("Paste Gemini API Key:", type="password")

st.sidebar.info("Class 12 Investigatory Project Prototype")

# 4. Image Upload Button
uploaded_file = st.file_uploader("📸 Upload or Take a Photo of an Ingredient Label", type=["jpg", "jpeg", "png"])

# 5. Display Image & Analyze
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)

    if st.button("🚀 Analyze Ingredients Now", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please add your API key in Streamlit Secrets or the sidebar first!")
        else:
            with st.spinner("🔬 Scanning chemicals, checking conflicts, and calculating Eco-Score..."):
                try:
                    client = genai.Client(api_key=api_key)

                    # Resize large phone photos so the API processes them faster and fails less
                    api_image = image.copy()
                    api_image.thumbnail((1024, 1024))

                    prompt = """
                    Look at the ingredients in this image and create an original student summary report.
                    CRITICAL RULE: Do NOT transcribe or copy the ingredient list word-for-word from the image, as copying packaging text triggers copyright filters.

                    Instead, analyze the image and write a brief, original summary using these exact headers with emojis:

                    ### 🧪 1. INGREDIENT OVERVIEW
                    Group the main ingredients you see into simple categories (e.g., "Base liquids", "Sweeteners", "Preservatives") using your own words. Do not list them in the exact order shown on the package.

                    ### ⚠️ 2. TOXIC & HEALTH ISSUES
                    Point out any unhealthy chemicals you spot (like Parabens, Phthalates, Trans Fats, high sugar/sodium, or artificial dyes) and briefly explain in simple words how they affect the body.

                    ### 🥜 3. ALLERGEN DETECTION
                    Note any common allergens present (like nuts, dairy, soy, gluten, or strong fragrances).

                    ### 💥 4. CONFLICT CHECKER
                    Mention if any ingredients in this mix react poorly together or irritate the body when combined.

                    ### 🤥 5. DECEPTIVE MARKETING
                    Point out any hidden sugars, diluted ingredients, or sneaky chemical names.

                    ### 🌍 6. ECO & BODY SCORE (1-10)
                    Give an overall rating out of 10 for health and environment, and explain why in 2 sentences.

                    ### ✅ 7. ALTERNATIVE RECOMMENDATIONS
                    Suggest 2 healthier or more natural alternatives.
                    """

                    # Automatic fallback list: if one model is overloaded (503), jump to the next
                    models_to_try = [
                        "gemini-3.8-flash",
                        "gemini-2.5-flash",
                        "gemini-2.5-flash-lite",
                        "gemini-2.0-flash",
                    ]

                    response = None
                    used_model = None
                    last_error = None

                    for model_name in models_to_try:
                        for attempt in range(2):
                            try:
                                response = client.models.generate_content(
                                    model=model_name,
                                    contents=[prompt, api_image],
                                    config=types.GenerateContentConfig(
                                        temperature=1.2,
                                        top_p=0.95
                                    )
                                )
                                used_model = model_name
                                break
                            except Exception as e:
                                last_error = e
                                if "503" in str(e) and attempt == 0:
                                    time.sleep(2)
                                else:
                                    break  # Switch to next backup model
                        if response is not None:
                            break

                    if response is None:
                        st.error(f"All AI models are currently busy. Last error: {last_error}")
                    elif response.text is None:
                        st.error(f"⚠️ The AI blocked the response! Reason: {response.candidates[0].finish_reason}")
                    else:
                        st.success(f"✅ Analysis Complete! (Powered by `{used_model}`)")
                        st.markdown("---")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")