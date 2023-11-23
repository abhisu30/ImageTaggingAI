import streamlit as st
import base64
import requests
import pandas as pd
from openai import OpenAI
from io import BytesIO

# Placeholder for the TagCreatorGPT function
def AltTagCreatorGPT(content, keyword, atagw):
    MODEL = "gpt-3.5-turbo-1106"
    instruction = f"""
    You are an expert in using a description of an image to create a custom Alt tag for the image.
    The Alt Tag must describe the image and state what the image is trying to convey to the person seeing the page.
    This is the description of the image: {content}.
    You will follow the below instrutions to create the tag.
    - You will use this description as a reference to create the Alt tag for the image.
    - The Alt tag must have {atagw} words in total.
    - The Alt tag must include this word: {keyword}.
    - Your reply must only contain the output text without special charachters. 
    - You must not mention the name of the tag.
    - You must not provide any explanation.
    """
    response = client.chat.completions.create(
    model=MODEL,
    messages=[
            {"role": "system", "content": "You are an image Alt tag creator."},
            {"role": "user", "content": instruction}
        ],
    temperature=0.3,
    )

    Alttag = response.choices[0].message.content
    
    return Alttag

def TitleTagCreatorGPT(content, keyword, ttagw):
    messages =[]
    MODEL = "gpt-3.5-turbo-1106"

    instruction = f"""
    You are an expert in using a description of an image to create a Title tag for the image.
    This is the description of the image: {content}.
    You will follow the below instrutions to create the Title tag.
    - You will use the description as a reference to create the Title tag for the image.
    - The Title tag will have {ttagw} words in total.
    - The Title tag will include this word: {keyword}.
    - Your reply must only contain the output text without special charachters. 
    - You must not mention the name of the tag.
    - You must not provide any explanation.
    """
    response = client.chat.completions.create(
    model=MODEL,
    messages=[
            {"role": "system", "content": "You are an image Title tag creator."},
            {"role": "user", "content": instruction}
        ],
    temperature=0.3
    )

    TitleTag = response.choices[0].message.content
    return TitleTag

# Function to encode the image
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# Function to get MIME type based on file extension
def get_mime_type(file_name):
    if file_name.lower().endswith(('.png', '.apng')):
        return "image/png"
    elif file_name.lower().endswith(('.jpg', '.jpeg', '.jfif', '.pjpeg', '.pjp')):
        return "image/jpeg"
    else:
        # Default to JPEG if unknown
        return "image/jpeg"

# Streamlit UI components
st.title("AI Image Optimizer")

# API Key Input
apikey = st.text_input("Enter API Key", type="password")

client = OpenAI(api_key=apikey)

# Additional fields
keyword = st.text_input("Add Keyword/s (comma separated)", "Enter keyword")
ttagw = st.number_input("Max words in Title Tag", min_value=1, value=5, step=1)
atagw = st.number_input("Max words in Alt Tag", min_value=1, value=5, step=1, key='atagw')
uploaded_files = st.file_uploader("Upload Image/s", accept_multiple_files=True)

# Process button
if st.button("Process"):
    # Check if API key and files are uploaded
    if apikey and uploaded_files:
        results = []

        # Process each image
        for uploaded_file in uploaded_files:
            # Getting the base64 string
            base64_image = encode_image(uploaded_file)
            mime_type = get_mime_type(uploaded_file.name)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {apikey}"
            }

            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                  {
                    "role": "user",
                    "content": [
                      {
                        "type": "text",
                        "text": f"Describe the image in less than {ttagw+1} words using the term - {keyword}"
                      },
                      {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "low",
                        }
                      }
                    ]
                  }
                ],
                "max_tokens": 300
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response_json = response.json()

            # Extract 'content' from response
            content = response_json['choices'][0]['message']['content']
            Alttag = AltTagCreatorGPT(content, keyword, atagw)
            TitleTag = TitleTagCreatorGPT(content, keyword, ttagw)
            results.append((uploaded_file.name, Alttag, TitleTag))

        # Create a DataFrame for results and display it with custom column names
        df_results = pd.DataFrame(results, columns=['Image', 'Alt Tag', 'Title Tag'])
        st.write("Results:")
        st.table(df_results)

        # Convert DataFrame to Excel
        output = BytesIO()
        # Convert DataFrame to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_results.to_excel(writer, index=False)
        val = output.getvalue()

        # Create a download button
        st.download_button(
            label="Download Excel",
            data=val,
            file_name="image_tags.xlsx",
            mime="application/vnd.ms-excel"
        )

    else:
        st.warning("Please enter an API key and upload at least one image.")
