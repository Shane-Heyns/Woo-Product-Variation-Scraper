from requests_html import HTMLSession
import csv
from unidecode import unidecode

s = HTMLSession()

def get_product_links(page):
    url = f'https://WOO_SHOP_LINK/page/{page}/'
    links = []
    r = s.get(url)
    products = r.html.find('div.wd-products .product')
    for item in products:
        links.append(item.find('a', first=True).attrs['href'])
    return links

def extract_categories(r):
    categories = []
    breadcrumb_items = r.html.find('.woocommerce-breadcrumb span a')
    if breadcrumb_items:
        for item in breadcrumb_items[1:-1]:
            categories.append(item.full_text.strip())
    return ' > '.join(categories)

def extract_images(r):
    image_list = []
    image_elements = r.html.find('.woocommerce-product-gallery__image a')
    for img in image_elements:
        try:
            image_list.append(img.find('a', first=True).attrs['href'])
        except KeyError:
            print("Image src attribute not found")
            continue
    return ', '.join(image_list)

def extract_variations(r, parent_sku):
    variations = []
    
    # Extract color variations
    color_elements = r.html.find('span.wd-swatch-text')
    colors = [color.full_text.strip() for color in color_elements]
    
    # Extract size variations
    size_element = r.html.find('select#pa_size', first=True)
    sizes = []
    if size_element:
        size_options = size_element.find('option')
        sizes = [option.full_text.strip() for option in size_options if option.attrs.get('value')]
    
    # Generate variations
    for color in colors:
        for size in sizes:
            variation_sku = f"{parent_sku}-{color[0].upper()}-{size}"
            variation = {
                'Type': 'variation',
                'SKU': variation_sku,
                'Name': '',  # Variation name can be left empty or derived from parent
                'Weight (kg)': '',
                'Length (cm)': '',
                'Width (cm)': '',
                'Height (cm)': '',
                'Description': '',  # Variations inherit parent description
                'Categories': '',  # Variations inherit parent categories
                'Images': '',  # Variations inherit parent images
                'Parent': parent_sku,
                'Attribute 1 name': 'Color',
                'Attribute 1 value(s)': color,
                'Attribute 1 visible': '1',
                'Attribute 1 global': '1',
                'Attribute 2 name': 'Size',
                'Attribute 2 value(s)': size,
                'Attribute 2 visible': '1',
                'Attribute 2 global': '1',
            }
            variations.append(variation)
    
    return variations

def parse_product(url):
    r = s.get(url)
    title = r.html.find('h1.product_title', first=True).full_text.strip()
    product_desc = unidecode(r.html.find('div.woocommerce-product-details__short-description', first=True).full_text) if r.html.find('div.woocommerce-product-details__short-description', first=True) else ""
    try:
        sku = r.html.find('span.sku', first=True).full_text.strip()
    except AttributeError:
        sku = ''
    
    categories = extract_categories(r)
    images = extract_images(r)
    
    # Check if the product has variations
    variations = []
    if r.html.find('select#pa_size', first=True) and r.html.find('span.wd-swatch-text', first=True):
        variations = extract_variations(r, sku)
    
    # Create parent product
    parent_product = {
        'Type': 'parent',
        'SKU': sku,
        'Name': title,
        'Weight (kg)': '',
        'Length (cm)': '',
        'Width (cm)': '',
        'Height (cm)': '',
        'Description': product_desc.strip(),
        'Categories': categories,
        'Images': images,
        'Parent': '',
        'Attribute 1 name': '',
        'Attribute 1 value(s)': '',
        'Attribute 1 visible': '',
        'Attribute 1 global': '',
        'Attribute 2 name': '',
        'Attribute 2 value(s)': '',
        'Attribute 2 visible': '',
        'Attribute 2 global': '',
    }
    
    # Return parent product and variations
    return [parent_product] + variations

def save_csv(results):
    keys = results[0].keys()
    with open('woo_products.csv', 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)

def main():
    results = []
    for x in range(232, 233):  # Adjust the page range as needed
        print('Getting Page:', x)
        urls = get_product_links(x)
        for url in urls:
            results.extend(parse_product(url))
        print('Total Results: ', len(results))
    save_csv(results)

if __name__ == '__main__':
    main()
