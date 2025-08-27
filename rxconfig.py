import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="reflex1",
    plugins=[
        SitemapPlugin(),
    ],
    # Add these lines to specify the ports
    frontend_port=3000,
    backend_port=8000
)