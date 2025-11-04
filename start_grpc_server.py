"""
Start gRPC Authentication Server
Run this script to start the authentication service
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the server
from api.grpc_services.auth_service import serve

if __name__ == '__main__':
    print("Starting gRPC Authentication Server...")
    try:
        serve(port=50051)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
