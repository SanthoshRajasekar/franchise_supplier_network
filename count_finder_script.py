import os,sys
import pandas as pd
from lxml import html

def count_links_and_images(html_content):
    tree = html.fromstring(html_content)

    # Count images and links
    num_images = len(tree.xpath('//img/@src'))
    num_links = len(tree.xpath('//a/@href'))

    return num_images, num_links

def process_directory(directory_path):
    # Prepare a list to hold data
    data = []

    # Loop through all txt files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                html_content = file.read()

            # Count images and links in the file
            num_images, num_links = count_links_and_images(html_content)
            data.append({"Filename": filename.split('_')[0], "Number of Images": num_images, "Number of URLs": num_links})

    # Convert list to DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv('link_and_image_counts.csv', index=False)

# Example usage
directory_path = sys.argv[1]
process_directory(directory_path)
