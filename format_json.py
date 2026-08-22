import json
import sys

def process(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    button_html = '\n\n<a href="https://www.optimatrix.in/portfolio" target="_blank" class="btn btn-primary" style="display: inline-block; padding: 10px 20px; margin-top: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #007bff; color: white;">View Our Portfolio →</a>'
    
    for item in data:
        if 'responses' in item:
            for i in range(len(item['responses'])):
                response = item['responses'][i]
                if '[View Portfolio]' in response or '[View All Projects]' in response or '[View Web Portfolio]' in response or '[View App Portfolio]' in response or '[View Case Studies]' in response or '[View Before After Work]' in response or '[View Design Portfolio]' in response or '[View eCommerce Portfolio]' in response or '[View Recent Work]' in response:
                    parts = response.split('\n\n[')
                    item['responses'][i] = parts[0] + button_html
                    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

process(r'c:\Users\Lenovo\Desktop\Testing\backend\JSON_Data\Portfolio_Data\portfolio_data.json')
