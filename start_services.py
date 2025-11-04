"""
Startup script for autonomous research agent
Runs both gRPC auth service and FastAPI server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_grpc_server():
    """Start the gRPC authentication server"""
    print("🚀 Starting gRPC Authentication Server...")
    grpc_process = subprocess.Popen(
        [sys.executable, "-m", "api.grpc_services.auth_service"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait a moment for server to start
    time.sleep(2)
    
    if grpc_process.poll() is None:
        print("✓ gRPC server started successfully on port 50051")
    else:
        print("✗ Failed to start gRPC server")
        stderr = grpc_process.stderr.read()
        print(f"Error: {stderr}")
        return None
    
    return grpc_process

def start_fastapi_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI Server...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait a moment for server to start
    time.sleep(2)
    
    if api_process.poll() is None:
        print("✓ FastAPI server started successfully on port 8000")
        print("\n" + "="*60)
        print("🎉 All services running!")
        print("="*60)
        print("📝 API Documentation: http://localhost:8000/docs")
        print("🔐 gRPC Auth Service: localhost:50051")
        print("="*60 + "\n")
    else:
        print("✗ Failed to start FastAPI server")
        return None
    
    return api_process

def main():
    """Main startup function"""
    print("\n" + "="*60)
    print("  Autonomous Research Agent - Starting Services")
    print("="*60 + "\n")
    
    # Start gRPC server
    grpc_proc = start_grpc_server()
    if not grpc_proc:
        print("\n❌ Startup failed - gRPC server did not start")
        return 1
    
    # Start FastAPI server
    api_proc = start_fastapi_server()
    if not api_proc:
        print("\n❌ Startup failed - FastAPI server did not start")
        grpc_proc.terminate()
        return 1
    
    try:
        # Keep running and monitor processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if grpc_proc.poll() is not None:
                print("\n⚠️  gRPC server stopped unexpectedly")
                api_proc.terminate()
                return 1
            
            if api_proc.poll() is not None:
                print("\n⚠️  FastAPI server stopped unexpectedly")
                grpc_proc.terminate()
                return 1
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        grpc_proc.terminate()
        api_proc.terminate()
        
        # Wait for graceful shutdown
        grpc_proc.wait(timeout=5)
        api_proc.wait(timeout=5)
        
        print("✓ All services stopped")
        print("Goodbye! 👋\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())
