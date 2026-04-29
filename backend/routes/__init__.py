"""
Routes package for Amen! API.

Each module in this package registers endpoints on the shared `api_router`
imported from core.py. The modules must be imported by server.py before
`app.include_router(api_router)` is called.
"""
