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
        num_items = len(breadcrumb_items)
        if num_items > 2:
            for item in breadcrumb_items[1:]:
                categories.append(item.full_text.strip())
        elif num_items == 2:
            categories.append(breadcrumb_items[1].full_text.strip())

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
    try:
        brands = r.html.find('div.wd-product-brands', first=True).full_text.strip()
    except AttributeError:
        brands = ''

    product_data = {
        'Type': 'variable',  # Parent product is 'variable'
        'SKU': sku,
        'Name': title,
        'Weight (kg)': '',
        'Length (cm)': '',
        'Width (cm)': '',
        'Height (cm)': '',
        'Description': product_desc.strip(),
        'Categories': categories,
        'Images': images,
        'Brands': brands,
        'Parent': '',
        'Attribute 1 name': 'Color',
        'Attribute 1 value(s)': '',
        'Attribute 1 visible': '1',
        'Attribute 1 global': '1',
        'Attribute 2 name': 'Size',
        'Attribute 2 value(s)': '',
        'Attribute 2 visible': '1',
        'Attribute 2 global': '1',
    }

    products = [product_data]

    color_options = [option.attrs['value'] for option in r.html.find('.product-image-summary-wrap #pa_color option') if option.attrs.get('value') != ""]
    size_options = [option.attrs['value'] for option in r.html.find('.product-image-summary-wrap #pa_size option') if option.attrs.get('value') != ""]

    if color_options and size_options:
        for color in color_options:
            for size in size_options:
                variation_sku = f"{sku}-{color[0].upper()}-{size}"
                variation_name = f"{title} - {color} - {size}"
                variation = {
                    'Type': 'variation',  # Variation is 'variation'
                    'SKU': variation_sku,
                    'Name': variation_name,
                    'Weight (kg)': '',
                    'Length (cm)': '',
                    'Width (cm)': '',
                    'Height (cm)': '',
                    'Description': '',
                    'Categories': categories,
                    'Images': images,
                    'Brands': brands,
                    'Parent': sku,
                    'Attribute 1 name': 'Color',
                    'Attribute 1 value(s)': color,
                    'Attribute 1 visible': '1',
                    'Attribute 1 global': '1',
                    'Attribute 2 name': 'Size',
                    'Attribute 2 value(s)': size,
                    'Attribute 2 visible': '1',
                    'Attribute 2 global': '1',
                }
                products.append(variation)

    elif color_options and not size_options:
        for color in color_options:
            variation_sku = f"{sku}-{color[0].upper()}"
            variation_name = f"{title} - {color}"
            variation = {
                'Type': 'variation',  # Variation is 'variation'
                'SKU': variation_sku,
                'Name': variation_name,
                'Weight (kg)': '',
                'Length (cm)': '',
                'Width (cm)': '',
                'Height (cm)': '',
                'Description': '',
                'Categories': categories,
                'Images': images,
                'Brands': brands,
                'Parent': sku,
                'Attribute 1 name': 'Color',
                'Attribute 1 value(s)': color,
                'Attribute 1 visible': '1',
                'Attribute 1 global': '1',
                'Attribute 2 name': 'Size',
                'Attribute 2 value(s)': '',
                'Attribute 2 visible': '1',
                'Attribute 2 global': '1',
            }
            products.append(variation)

    elif not color_options and size_options:
        for size in size_options:
            variation_sku = f"{sku}--{size}"
            variation_name = f"{title} - {size}"
            variation = {
                'Type': 'variation',  # Variation is 'variation'
                'SKU': variation_sku,
                'Name': variation_name,
                'Weight (kg)': '',
                'Length (cm)': '',
                'Width (cm)': '',
                'Height (cm)': '',
                'Description': '',
                'Categories': categories,
                'Images': images,
                'Brands': brands,
                'Parent': sku,
                'Attribute 1 name': 'Color',
                'Attribute 1 value(s)': '',
                'Attribute 1 visible': '1',
                'Attribute 1 global': '1',
                'Attribute 2 name': 'Size',
                'Attribute 2 value(s)': size,
                'Attribute 2 visible': '1',
                'Attribute 2 global': '1',
            }
            products.append(variation)

    else:
        product_data['Type'] = 'simple'
        return products

    return products

def save_csv(results):
    all_products = []
    for product_list in results:
        all_products.extend(product_list)

    if all_products:
        keys = all_products[0].keys()
        with open('woo_products.csv', 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_products)
    else:
        print("No products found to save.")

def main():
    results = []
    #how many pages must it go through for 232 pages range will be (1, 233)
    for x in range(235, 236):
        print('Getting Page:', x)
        urls = get_product_links(x)
        for url in urls:
            results.append(parse_product(url))
        print('Total Results: ', len(results))
    save_csv(results)

if __name__ == '__main__':
    main()
