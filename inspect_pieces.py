import inspect
import pprint
from pieceLibrary import mainPieceLibrary, patchworkPieceLibrary, test_piece_library

def inspect_piece(piece_id, piece_obj):
    """Inspect a piece object and print its structure"""
    print(f"\n=== Piece: {piece_id} ===")
    print(f"Type: {type(piece_obj)}")
    
    # Check for common attributes
    attrs = ['color', 'coords', '_coords']
    for attr in attrs:
        if hasattr(piece_obj, attr):
            print(f"Has {attr}: {getattr(piece_obj, attr)}")
    
    # Check for methods
    if hasattr(piece_obj, 'get_offsets') and callable(getattr(piece_obj, 'get_offsets')):
        try:
            offsets = piece_obj.get_offsets()
            print(f"get_offsets() returns: {offsets}")
        except Exception as e:
            print(f"Error calling get_offsets(): {str(e)}")
    
    # Print all attributes that aren't methods or dunder methods
    print("\nAll attributes:")
    for name, value in inspect.getmembers(piece_obj):
        if not name.startswith('__') and not callable(value):
            print(f"  {name}: {type(value)}")
            if isinstance(value, list) and len(value) < 20:  # Only print short lists
                print(f"    Value: {value}")
    
    print("\n")

def extract_piece_offsets(piece_obj):
    """Try to extract piece offsets using multiple methods"""
    results = {}
    
    # Method 1: Using get_offsets
    if hasattr(piece_obj, 'get_offsets') and callable(getattr(piece_obj, 'get_offsets')):
        try:
            results['get_offsets'] = piece_obj.get_offsets()
        except Exception as e:
            results['get_offsets_error'] = str(e)
    
    # Method 2: Using coords attribute
    if hasattr(piece_obj, 'coords'):
        coords = piece_obj.coords
        offsets = []
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                offsets.append([coords[i], coords[i+1]])
        results['coords_attribute'] = offsets
    
    # Method 3: Using _coords attribute
    if hasattr(piece_obj, '_coords'):
        coords = piece_obj._coords
        offsets = []
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                offsets.append([coords[i], coords[i+1]])
        results['_coords_attribute'] = offsets
    
    # Method 4: Using coordinate attributes
    for name, value in inspect.getmembers(piece_obj):
        if isinstance(value, list) and len(value) > 0 and all(isinstance(x, int) for x in value) and not name.startswith('__'):
            if len(value) % 2 == 0:  # Ensure we have pairs
                offsets = []
                for i in range(0, len(value), 2):
                    offsets.append([value[i], value[i+1]])
                results[f'attribute_{name}'] = offsets
    
    return results

def main():
    # First, let's check the mainPieceLibrary
    print("==== MAIN PIECE LIBRARY ====")
    for piece_id, piece_obj in mainPieceLibrary.items():
        print(f"\nPiece ID: {piece_id}")
        all_extractions = extract_piece_offsets(piece_obj)
        pprint.pprint(all_extractions)
    
    # Then check the patchworkPieceLibrary
    print("\n\n==== PATCHWORK PIECE LIBRARY ====")
    for piece_id, piece_obj in patchworkPieceLibrary.items():
        print(f"\nPiece ID: {piece_id}")
        all_extractions = extract_piece_offsets(piece_obj)
        pprint.pprint(all_extractions)
    
    # Check for any pieces that have no extractable coordinates
    print("\n\n==== PIECES WITH NO EXTRACTABLE COORDINATES ====")
    for library_name, library in [
        ("mainPieceLibrary", mainPieceLibrary),
        ("patchworkPieceLibrary", patchworkPieceLibrary),
        ("test_piece_library", test_piece_library)
    ]:
        for piece_id, piece_obj in library.items():
            extractions = extract_piece_offsets(piece_obj)
            if not extractions:
                print(f"{library_name} - {piece_id}")
                inspect_piece(piece_id, piece_obj)

if __name__ == "__main__":
    main() 