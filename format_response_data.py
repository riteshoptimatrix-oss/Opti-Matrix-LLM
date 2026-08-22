import json

file_path = r'c:\Users\Lenovo\Desktop\Testing\backend\response_data.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

changed = False
button_html = '\n\n<a href="https://www.optimatrix.in/portfolio" target="_blank" class="btn btn-primary" style="display: inline-block; padding: 10px 20px; margin-top: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; background-color: #007bff; color: white;">View Our Portfolio →</a>'

for k, responses in data.items():
    for i in range(len(responses)):
        response = responses[i]
        if 'portfolio' in response.lower() or 'portfolio' in k.lower():
            if '[View Portfolio]' in response or 'https://www.optiinfo.com/our-portfolio/' in response or 'https://www.optimatrix.in/portfolio' in response:
                if 'class="btn btn-primary"' not in response:
                    # simplistic replace
                    parts = response.split('\n\n[')
                    if len(parts) == 1:
                        parts = response.split('\n[')
                    responses[i] = parts[0] + button_html
                    changed = True

if changed:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print('Updated response_data.json')
else:
    print('No changes needed in response_data.json')
