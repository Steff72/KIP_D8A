from PIL import Image
import sys

def remove_background(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    for item in datas:
        # Calculate distance from black
        # Euclidean distance would be sqrt(r^2 + g^2 + b^2)
        # Simple sum is faster: r + g + b
        brightness = item[0] + item[1] + item[2]
        
        # Threshold of 180 (roughly 60 per channel)
        if brightness < 180:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(output_path, "PNG")
    print(f"Saved transparent image to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python remove_background.py <input_path> <output_path>")
    else:
        remove_background(sys.argv[1], sys.argv[2])
