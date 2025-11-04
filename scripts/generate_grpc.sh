#!/bin/bash
# Generate Python code from Protocol Buffer definitions

echo "🔨 Generating gRPC code from protobuf definitions..."

python -m grpc_tools.protoc \
    -I./grpc-protos \
    --python_out=./grpc_generated \
    --grpc_python_out=./grpc_generated \
    ./grpc-protos/auth.proto

if [ $? -eq 0 ]; then
    echo "✅ gRPC code generated successfully!"
    echo "Generated files:"
    echo "  - grpc_generated/auth_pb2.py"
    echo "  - grpc_generated/auth_pb2_grpc.py"
else
    echo "❌ Failed to generate gRPC code"
    echo "Make sure grpcio-tools is installed: pip install grpcio-tools"
fi
