"""
Simple test script for the REST API endpoints.
"""

import sys
sys.path.insert(0, 'src')

from ontology.api import create_app
import json

def test_api():
    """Test the API endpoints."""
    print("=" * 70)
    print("Testing REST API Endpoints")
    print("=" * 70)
    
    # Create app in test mode
    app = create_app({'TESTING': True})
    client = app.test_client()
    
    # Test 1: Health check
    print("\n1. Testing GET /health")
    response = client.get('/health')
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Components: {data['data']['components']}")
    assert response.status_code == 200
    assert data['success'] == True
    print("   ✓ Health check passed")
    
    # Test 2: Load files
    print("\n2. Testing POST /load")
    response = client.post('/load', 
        json={
            'files': ['ontology/core.ttl', 'ontology/extensions.ttl'],
            'validate': True
        },
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Message: {data['message']}")
    if 'data' in data:
        print(f"   Files loaded: {data['data'].get('total_loaded', 0)}")
    assert response.status_code in [200, 207]
    print("   ✓ Load endpoint passed")
    
    # Test 3: Query endpoint (with validation error expected)
    print("\n3. Testing POST /query (validation error expected)")
    response = client.post('/query',
        json={},
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Error: {data.get('error', {}).get('message', 'N/A')}")
    assert response.status_code == 400
    assert data['success'] == False
    print("   ✓ Query validation passed")
    
    # Test 4: Query endpoint (with valid query)
    print("\n4. Testing POST /query (with valid query)")
    response = client.post('/query',
        json={
            'query': 'SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10'
        },
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Message: {data['message']}")
    assert response.status_code == 200
    print("   ✓ Query execution passed")
    
    # Test 5: Validate endpoint (no shapes loaded)
    print("\n5. Testing POST /validate (no shapes)")
    response = client.post('/validate',
        json={},
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Error: {data.get('error', {}).get('message', 'N/A')}")
    assert response.status_code == 400
    print("   ✓ Validation error handling passed")
    
    # Test 6: Validate endpoint (with shapes file)
    print("\n6. Testing POST /validate (with shapes)")
    response = client.post('/validate',
        json={
            'shapes_file': 'validation/shapes.ttl'
        },
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Message: {data['message']}")
    if 'data' in data:
        print(f"   Conforms: {data['data'].get('conforms', 'N/A')}")
    assert response.status_code == 200
    print("   ✓ Validation passed")
    
    # Test 7: Get triples
    print("\n7. Testing GET /triples")
    response = client.get('/triples')
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Message: {data['message']}")
    if 'data' in data:
        print(f"   Files: {data['data'].get('file_count', 0)}")
    assert response.status_code == 200
    print("   ✓ Get triples passed")
    
    # Test 8: Delete triples (clear all)
    print("\n8. Testing DELETE /triples (clear all)")
    response = client.delete('/triples',
        json={'clear_all': True},
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Message: {data['message']}")
    assert response.status_code == 200
    print("   ✓ Delete triples passed")
    
    # Test 9: 404 error
    print("\n9. Testing 404 error handling")
    response = client.get('/nonexistent')
    print(f"   Status: {response.status_code}")
    data = json.loads(response.data)
    print(f"   Success: {data['success']}")
    print(f"   Error: {data.get('error', {}).get('message', 'N/A')}")
    assert response.status_code == 404
    assert data['success'] == False
    print("   ✓ 404 handling passed")
    
    print("\n" + "=" * 70)
    print("All API tests passed! ✓")
    print("=" * 70)


if __name__ == '__main__':
    try:
        test_api()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
