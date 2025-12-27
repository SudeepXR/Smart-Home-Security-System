import os
import google.generativeai as genai

print("Key exists:", bool(os.environ.get("GOOGLE_API_KEY")))

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")
res = model.generate_content("Say OK")
print(res.text)
