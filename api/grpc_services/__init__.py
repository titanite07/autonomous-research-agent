"""gRPC Services Package"""

from .grpc_client import AuthGRPCClient, get_grpc_auth_client

__all__ = ['AuthGRPCClient', 'get_grpc_auth_client']
