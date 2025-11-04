"""
Standalone gRPC Server Launcher
Run this alongside FastAPI to provide gRPC authentication
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.grpc_services.auth_service import serve

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='gRPC Authentication Server')
    parser.add_argument('--port', type=int, default=50051, help='Port to run gRPC server on')
    args = parser.parse_args()
    
    print(f'🚀 Starting gRPC Authentication Server on port {args.port}...')
    serve(port=args.port)
