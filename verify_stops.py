from app import get_distance_multiplier, MUMBAI_AREAS_MAP, MUMBAI_AREAS

def test_pricing():
    print("Testing Pricing Logic...")
    
    # Test 1: Same area
    m1 = get_distance_multiplier('Colaba Bus Station', 'Electric House')
    print(f"Colaba Bus Station -> Electric House: {m1} (Expected: 0.8)")
    
    # Test 2: Near area
    m2 = get_distance_multiplier('Colaba Bus Station', 'Grant Road Station')
    # Colaba(0), Churchgate(1), Marine Lines(2), Charni Road(3), Grant Road(4) -> Gap = 4
    print(f"Colaba Bus Station -> Grant Road Station: {m2} (Expected: 1.0)")
    
    # Test 3: Long distance
    m3 = get_distance_multiplier('Colaba Bus Station', 'Bandra West')
    # Colaba(0) -> Bandra(19) -> Gap = 19
    print(f"Colaba Bus Station -> Bandra West: {m3} (Expected: 1.5)")
    
    # Test 4: Santacruz specific
    m4 = get_distance_multiplier('Milan Subway', 'Vakola Police Station')
    print(f"Milan Subway -> Vakola Police Station: {m4} (Expected: 0.8)")
    
    # Test 5: Santacruz to Bandra
    m5 = get_distance_multiplier('Santacruz West', 'Bandra West')
    # Santacruz(21), Bandra(19) -> Gap = 2
    print(f"Santacruz West -> Bandra West: {m5} (Expected: 1.0)")

if __name__ == "__main__":
    test_pricing()
