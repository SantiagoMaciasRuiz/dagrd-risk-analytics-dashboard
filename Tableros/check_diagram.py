with open(r'_pbix_extract_temp\DiagramLayout', 'rb') as f:
    first_bytes = f.read(100)
    print(f"Primeros bytes (hex): {first_bytes.hex()}")
    print(f"File signature: {first_bytes[:4]}")
