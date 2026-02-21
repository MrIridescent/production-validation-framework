#!/usr/bin/env python3
"""
🔌 REAL API CLIENT MODULE
=========================
Provides production-grade synchronous and asynchronous API clients.
"""

import requests
import httpx
import asyncio
from typing import Dict, Any, Optional

class SyncAPIClient:
    """Synchronous API client using requests"""
    def get(self, url: str, **kwargs) -> requests.Response:
        return requests.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        return requests.post(url, **kwargs)
        
    def put(self, url: str, **kwargs) -> requests.Response:
        return requests.put(url, **kwargs)
        
    def delete(self, url: str, **kwargs) -> requests.Response:
        return requests.delete(url, **kwargs)

class AsyncAPIClient:
    """Asynchronous API client using httpx"""
    async def get(self, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.get(url, **kwargs)
            
    async def post(self, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.post(url, **kwargs)
            
    async def put(self, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.put(url, **kwargs)
            
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.delete(url, **kwargs)

# Singleton instances
sync_client = SyncAPIClient()
async_client = AsyncAPIClient()
