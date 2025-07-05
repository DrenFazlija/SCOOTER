from openai import OpenAI
import base64
import os
import json
from pathlib import Path
from tqdm import tqdm
import argparse
from dotenv import load_dotenv

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def process_image(image_path, client, system_prompt):
    try:
        base64_image = encode_image(image_path)
        response = client.responses.create(
            model="gpt-4o",
            input=[{
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Rate this image on a scale from -2 (definitely modified) to +2 (definitely real). Output only the number."},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    },
                ],
            }],
        )
        return response.output_text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None

def process_directory(directory_path, client, system_prompt):
    results = {}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    # Create directory if it doesn't exist
    os.makedirs(directory_path, exist_ok=True)
    
    # Process all images in the directory
    for file_path in tqdm(Path(directory_path).glob('*'), desc="Processing images"):
        if file_path.suffix.lower() in image_extensions:
            print(f"Processing {file_path.name}...")
            rating = process_image(str(file_path), client, system_prompt)
            if rating is not None:
                results[file_path.name] = rating
    
    # Save results to a JSON file
    output_file = os.path.join(directory_path, 'ratings.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    return results
    
def get_system_prompt():
    return """You are an expert image assessment assistant. Your task is to analyze images and rate them on a scale from -2 to +2:

    -2: Definitely modified (clear evidence of manipulation)
    -1: Probably modified (some signs of modification)
    0: Unsure (cannot determine with confidence)
    +1: Probably real (appears unmodified but with some uncertainty)
    +2: Definitely real (clear evidence of being unmodified)

    Follow these guidelines for assessment:

    1. Real/Unmodified Images:
    - Photographs captured using cameras or imaging devices
    - Show scenes or objects as they naturally exist
    - May have lower quality or unusual colors due to artificial lighting
    - May appear less clear than modern images

    2. Modified Images (consider these for negative ratings):
    - Use of filters (Instagram, Snapchat, etc.)
    - Partial or complete recoloring
    - Addition or removal of objects
    - Defective ("dead") pixels or other pixel changes
    - Unusual or unnatural coloring (e.g., greyscale)
    - Non-color related modifications (e.g., unusually sharp edges)
    - Minimal and subtle signs of modifications (inconsistent coloring, unusual lines)

    3. Important Considerations:
    - Some modifications are obvious, while others are subtle
    - Real images may have lower quality due to being from early 2000s
    - Indoor images may have unnatural colors due to artificial lighting
    - If an image looks like it's straight out of a camera without filters, it's likely unmodified

    Output ONLY the numerical rating (-2 to +2) with no additional text or explanation."""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--img_dir", type=str, required=True)
    args = parser.parse_args()

    load_dotenv()
    client = OpenAI(
        api_key = os.getenv("OPENAI_API_KEY")
    )

    system_prompt = get_system_prompt()

    # Process all images in the semanticadv directory
    results = process_directory(args.img_dir, client, system_prompt)