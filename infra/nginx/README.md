# Optional reverse proxy

The core runtime serves built frontend assets from FastAPI. A separate reverse-proxy deployment is deferred; no Nginx service or public TLS configuration is activated by the default Compose stack.
