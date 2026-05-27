# Standalone test for bus stop logic without external imports

MUMBAI_AREAS = [
    'Colaba', 'Churchgate', 'Marine Lines', 'Charni Road', 'Grant Road',
    'Mumbai Central', 'Mahalaxmi', 'Lower Parel', 'Parel', 'Dadar',
    'Matunga', 'Sion', 'Kurla', 'Ghatkopar', 'Vikhroli', 'Kanjurmarg',
    'Bhandup', 'Mulund', 'Thane', 'Bandra', 'Khar Road', 'Santa Cruz',
    'Vile Parle', 'Andheri', 'Jogeshwari', 'Goregaon', 'Malad',
    'Kandivali', 'Borivali', 'Dahisar', 'Mira Road', 'Chembur',
    'Wadala', 'Worli', 'Powai', 'Airoli', 'Vashi', 'Nerul',
    'Belapur', 'Panvel'
]

MUMBAI_AREAS_MAP = {
    'Colaba': ['Colaba Bus Station', 'Electric House', 'Regal Cinema', 'Sassoon Docks', 'Colaba'],
    'Churchgate': ['Churchgate Station', 'Mantralaya', 'Nariman Point', 'Marine Drive', 'Churchgate'],
    'Marine Lines': ['Marine Lines Station', 'Princess Street', 'Chandanwadi', 'Income Tax Office', 'Marine Lines'],
    'Charni Road': ['Charni Road Station', 'Opera House', 'Saifee Hospital', 'Girgaon Chowpatty', 'Charni Road'],
    'Grant Road': ['Grant Road Station', 'Nana Chowk', 'Tardeo Naka', 'Bhatia Hospital', 'Grant Road'],
    'Mumbai Central': ['Mumbai Central Station', 'Nair Hospital', 'Alexandra Cinema', 'Mahalaxmi Racecourse', 'Mumbai Central'],
    'Mahalaxmi': ['Mahalaxmi Station', 'Famous Studio', 'Nehru Planetarium', 'Mahalaxmi'],
    'Lower Parel': ['Lower Parel Station', 'High Street Phoenix', 'Kamala Mills', 'Deepak Cinema', 'Lower Parel'],
    'Parel': ['Parel Station', 'KEM Hospital', 'Tata Memorial Hospital', 'Parel'],
    'Dadar': ['Dadar West', 'Dadar East', 'Plaza Cinema', 'Shivaji Park', 'Siddhivinayak Temple', 'Dadar'],
    'Matunga': ['Matunga Station', 'Khalsa College', 'Five Gardens', 'Aurora Cinema', 'Matunga'],
    'Sion': ['Sion Station', 'Sion Circle', 'Chunabhatti', 'Somaiya College', 'Sion'],
    'Kurla': ['Kurla West', 'Kurla East', 'Phoenix Market City', 'BKC Connector', 'Kurla'],
    'Ghatkopar': ['Ghatkopar Station', 'R-City Mall', 'Pant Nagar', 'Sarvodaya Hospital', 'Ghatkopar'],
    'Vikhroli': ['Vikhroli Station', 'Godrej Colony', 'Kannamwar Nagar', 'Hiranandani Hospital', 'Vikhroli'],
    'Kanjurmarg': ['Kanjurmarg Station', 'Naval Dockyard Colony', 'IIT Main Gate', 'Kanjurmarg'],
    'Bhandup': ['Bhandup Station', 'Dreams Mall', 'Mangatram Petrol Pump', 'Bhandup'],
    'Mulund': ['Mulund West', 'Mulund East', 'Check Naka', 'Johnson & Johnson', 'Mulund'],
    'Thane': ['Thane Station', 'Teen Haath Naka', 'Viviana Mall', 'Cadbury Junction', 'Thane'],
    'Bandra': ['Bandra West', 'Bandra East', 'Bandra Reclamation', 'Lucky Hotel', 'Mount Mary Church', 'National College', 'BKC (G Block)', 'Bandra'],
    'Khar Road': ['Khar Road Station', 'Linking Road', 'Pali Hill', 'Khar Gymkhana', 'Khar Road'],
    'Santa Cruz': ['Santacruz West', 'Santacruz East', 'Milan Subway', 'Khira Nagar', 'Rizvi College', 'Vakola Police Station', 'Kalina Military Camp', 'Santa Cruz', 'Santacruz'],
    'Vile Parle': ['Vile Parle West', 'Vile Parle East', 'Mithibai College', 'Cooper Hospital', 'Juhu Beach', 'Vile Parle'],
    'Andheri': ['Andheri West', 'Andheri East', 'Shoppers Stop', 'Gilbert Hill', 'Seven Bungalows', 'Marol Naka', 'Saki Naka', 'Andheri'],
    'Jogeshwari': ['Jogeshwari West', 'Jogeshwari East', 'Oshiwara', 'Hub Mall', 'Jogeshwari'],
    'Goregaon': ['Goregaon West', 'Goregaon East', 'Film City Road', 'Oberoi Mall', 'Goregaon'],
    'Malad': ['Malad West', 'Malad East', 'Orlem', 'Infiniti Mall (Malad)', 'Marve Road', 'Malad'],
    'Kandivali': ['Kandivali West', 'Kandivali East', 'Thakur Village', 'Poisar', 'Kandivali'],
    'Borivali': ['Borivali West', 'Borivali East', 'Sanjay Gandhi National Park', 'Gorai Creek', 'Don Bosco School', 'Borivali'],
    'Dahisar': ['Dahisar West', 'Dahisar East', 'Anand Nagar', 'Kandarpada', 'Dahisar'],
    'Mira Road': ['Mira Road Station', 'Shanti Nagar', 'Beverly Park', 'Kashimira', 'Mira Road'],
    'Chembur': ['Chembur Station', 'Diamond Garden', 'Amar Mahal', 'Maitri Park', 'Chembur'],
    'Wadala': ['Wadala Station', 'Five Gardens (Wadala)', 'IMAX (Wadala)', 'Antop Hill', 'Wadala'],
    'Worli': ['Worli Naka', 'Worli Sea Face', 'Atria Mall', 'Nehru Centre', 'Worli'],
    'Powai': ['Powai Lake', 'IIT Bombay', 'Hiranandani Garden', 'Rambaug', 'Powai'],
    'Airoli': ['Airoli Station', 'Mindspace', 'Patni IT Park', 'Airoli'],
    'Vashi': ['Vashi Station', 'Sector 17', 'Inorbit Mall (Vashi)', 'APMC Market', 'Vashi'],
    'Nerul': ['Nerul Station', 'LP Bus Stop', 'DY Patil Stadium', 'Nerul'],
    'Belapur': ['Belapur Station', 'CBD Belapur', 'Uran Phata', 'Belapur'],
    'Panvel': ['Panvel Station', 'New Panvel', 'Old Panvel', 'Takka Colony', 'Panvel']
}

def get_area_for_stop(stop_name):
    for area, stops in MUMBAI_AREAS_MAP.items():
        if stop_name in stops:
            return area
    return stop_name

def get_distance_multiplier(route_from, route_to):
    area_from = get_area_for_stop(route_from)
    area_to = get_area_for_stop(route_to)

    if area_from not in MUMBAI_AREAS or area_to not in MUMBAI_AREAS:
        return 1.0
        
    idx_from = MUMBAI_AREAS.index(area_from)
    idx_to = MUMBAI_AREAS.index(area_to)
    gap = abs(idx_to - idx_from)
    
    if gap == 0:
        return 0.8
    elif gap <= 4:
        return 1.0
    elif gap <= 10:
        return 1.2
    else:
        return 1.5

def test_pricing():
    print("Testing Pricing Logic...")
    tests = [
        ('Colaba Bus Station', 'Electric House', 0.8),
        ('Colaba Bus Station', 'Grant Road Station', 1.0),
        ('Colaba Bus Station', 'Bandra West', 1.5),
        ('Milan Subway', 'Vakola Police Station', 0.8),
        ('Santacruz West', 'Bandra West', 1.0),
        ('Andheri West', 'Panvel Station', 1.5)
    ]
    
    for f, t, expected in tests:
        actual = get_distance_multiplier(f, t)
        status = "PASSED" if actual == expected else f"FAILED (Got {actual})"
        print(f"{f} -> {t}: {status}")

if __name__ == "__main__":
    test_pricing()
