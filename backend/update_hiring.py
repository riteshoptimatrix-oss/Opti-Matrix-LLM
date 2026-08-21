import json
import os
import glob
import re

def get_tech_name(filename):
    basename = os.path.basename(filename).replace('.json', '')
    # remove common suffixes
    name = basename.replace('_data', '').replace('_development', '').replace('_frameworks', '').replace('_framework', '').replace('_service', '')
    # replace underscores with spaces and title case
    name = name.replace('_', ' ').title()
    
    # Custom mappings
    if name.lower() == 'nodejs': return 'Node.js'
    if name.lower() == 'reactjs': return 'React.js'
    if name.lower() == 'nextjs': return 'Next.js'
    if name.lower() == 'angularjs': return 'Angular.js'
    if name.lower() == 'jquery': return 'jQuery'
    if name.lower() == 'php dev': return 'PHP'
    if name.lower() == 'php web': return 'PHP Web'
    if name.lower() == 'mobile app': return 'Mobile App'
    if name.lower() == 'web dev': return 'Web'
    if name.lower() == 'ajax': return 'AJAX'
    if name.lower() == 'html designing': return 'HTML'
    if name.lower() == 'psd layout': return 'PSD'
    if name.lower() == 'psd to html': return 'PSD to HTML'
    if name.lower() == 'mvc': return 'MVC'
    if name.lower() == 'iphone application': return 'iPhone'
    if name.lower() == 'ipad application': return 'iPad'
    if name.lower() == 'android application': return 'Android'
    if name.lower() == 'blackberry application': return 'BlackBerry'
    
    return name.strip()

base_dir = r'C:\Users\Lenovo\Desktop\Testing\backend\JSON_Data\Service_Data'
files = glob.glob(os.path.join(base_dir, '**', '*.json'), recursive=True)

updated_files = []

for f in files:
    if not os.path.isfile(f): continue
    
    with open(f, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except:
            continue
            
    tech_name = get_tech_name(f)
    
    hiring_intent_found = False
    for intent_obj in data:
        if 'hiring' in intent_obj['intent'] or 'hire' in intent_obj['intent']:
            hiring_intent_found = True
            pattern = f"I need to hire a {tech_name} developer"
            if pattern not in intent_obj['patterns']:
                intent_obj['patterns'].append(pattern)
            intent_obj['responses'] = [f"Opti Matrix houses a team of elite, highly experienced {tech_name} developers in India. We offer flexible hiring models (monthly, part-time, or hourly) providing you with top-tier talent, transparent communication, agile methodologies, and cost-effective solutions for your global projects. Contact our Head Office at <a href=\"tel:+918128361116\">+91 81283 61116</a> or email <a href=\"mailto:info@optimatrix.in\">info@optimatrix.in</a>."]

    if not hiring_intent_found:
        new_intent = {
            "intent": f"{tech_name.lower().replace(' ', '_')}_hiring",
            "patterns": [
                f"I need to hire a {tech_name} developer",
                f"Can I hire a dedicated {tech_name} developer?",
                f"Are your {tech_name} developers experienced?",
                f"Why choose Opti Matrix for {tech_name} development in India?"
            ],
            "responses": [
                f"Opti Matrix houses a team of elite, highly experienced {tech_name} developers in India. We offer flexible hiring models (monthly, part-time, or hourly) providing you with top-tier talent, transparent communication, agile methodologies, and cost-effective solutions for your global projects. Contact our Head Office at <a href=\"tel:+918128361116\">+91 81283 61116</a> or email <a href=\"mailto:info@optimatrix.in\">info@optimatrix.in</a>."
            ]
        }
        data.append(new_intent)
        
    with open(f, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)
    updated_files.append(f)

print(f"Updated {len(updated_files)} files")
