#!/bin/bash

echo "=== Testing POST /api/v1/tryon/direct endpoint ==="
echo ""
echo "This endpoint requires two image files: model_file and garment_file"
echo ""

# Check if test images exist
if [ ! -f "test_person.jpg" ]; then
    echo "Creating test person image..."
    python3 << 'PYEOF'
from PIL import Image
img = Image.new('RGB', (512, 512), color='red')
img.save('test_person.jpg')
print("✅ test_person.jpg created")
PYEOF
fi

if [ ! -f "test_garment.jpg" ]; then
    echo "Creating test garment image..."
    python3 << 'PYEOF'
from PIL import Image
img = Image.new('RGB', (512, 512), color='blue')
img.save('test_garment.jpg')
print("✅ test_garment.jpg created")
PYEOF
fi

echo ""
echo "Sending POST request to /api/v1/tryon/direct..."
echo ""

curl -X POST http://localhost:8500/api/v1/tryon/direct \
  -F "model_file=@test_person.jpg" \
  -F "garment_file=@test_garment.jpg" \
  -F "model_name=Test Person" \
  -F "garment_name=Test Garment" \
  | jq .

echo ""
echo "✅ Test complete"

