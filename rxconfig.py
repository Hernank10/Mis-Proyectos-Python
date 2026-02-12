import reflex as rx

config = rx.Config(
    app_name="Mis_Proyectos_Python",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)