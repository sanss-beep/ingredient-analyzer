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

# 4. Auto-Discover REAL Active Models on Your Exact API Key (Zero Guessing)
@st.cache_data(ttl=600, show_spinner=False)
def get_live_models(key):
    try:
        c = genai.Client(api_key=key)
        found = []
        skip_words = (
            "embedding", "imagen", "veo", "tts", "audio", "aqa",
            "robotics", "computer-use", "deep-research", "live"
        )
        for m in c.models.list():
            name = (m.name or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            supports_gen = ("generateContent" in actions) if actions else True
            if supports_gen and "gemini" in name.lower() and not any(w in name.lower() for w in skip_words):
                found.append(name)

        found.sort(reverse=True)  # Newest versions first
        flash_lite = [m for m in found if "flash-lite" in m]
        flash = [m for m in found if "flash" in m and "flash-lite" not in m]
        other = [m for m in found if "flash" not in m]
        ordered = flash_lite + flash + other
        return ordered if ordered else ["gemini-3.8-flash"]
    except Exception:
        return ["gemini-3.8-flash"]

available_models = get_live_models(api_key) if api_key else []
selected_mode = st.sidebar.selectbox(
    "🤖 AI Model:",
    ["Auto (Best Available)"] + available_models
)
if available_models:
    st.sidebar.caption(f"Detected {len(available_models)} live models on your key.")

st.sidebar.info("Class 12 Investigatory Project Prototype")

# 5. Image Upload Button
uploaded_file = st.file_uploader("📸 Upload or Take a Photo of an Ingredient Label", type=["jpg", "jpeg", "png"])

# 6. Display Image & Analyze
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

                    # Resize large phone photos for faster, more reliable uploads
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

                    if selected_mode == "Auto (Best Available)":
                        models_to_try = available_models[:6] if available_models else ["gemini-3.8-flash"]
                    else:
                        models_to_try = [selected_mode]

                    response = None
                    used_model = None
                    error_log = []

                    for model_name in models_to_try:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=[prompt, api_image],
                                config=types.GenerateContentConfig(
                                    temperature=1.0,
                                    top_p=0.95
                                )
                            )
                            used_model = model_name
                            break
                        except Exception as e:
                            error_log.append(f"- **`{model_name}`**: {e}")
                            time.sleep(1)

                    if response is None:
                        st.error("All available models failed. Exact breakdown:")
                        st.markdown("\n".join(error_log))
                    elif response.text is None:
                        st.error(f"⚠️ The AI blocked the response! Reason: {response.candidates[0].finish_reason}")
                    else:
                        st.success(f"✅ Analysis Complete! (Powered by `{used_model}`)")
                        st.markdown("---")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")