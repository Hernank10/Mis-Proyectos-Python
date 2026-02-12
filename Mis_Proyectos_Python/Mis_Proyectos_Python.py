import reflex as rx

class EstadoGramatica(rx.State):
    palabra: str = ""
    resultado: str = "Escribe una palabra..."

    def verificar_tilde(self):
        if not self.palabra:
            self.resultado = "Por favor, escribe algo."
            return
        ultima = self.palabra.lower()[-1]
        if ultima in "nsáéíóúaeiou":
            self.resultado = f"'{self.palabra}' podría llevar tilde si es aguda."
        else:
            self.resultado = f"'{self.palabra}' no lleva tilde si es aguda."

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("📚 GramatiCode", size="9", color_scheme="red"),
            rx.card(
                rx.vstack(
                    rx.input(placeholder="Palabra...", on_change=EstadoGramatica.set_palabra),
                    rx.button("Analizar", on_click=EstadoGramatica.verificar_tilde, width="100%"),
                    rx.text(EstadoGramatica.resultado, font_weight="bold"),
                ),
                padding="2em",
            ),
            rx.color_mode.button(position="top-right"),
        ),
        padding_top="10%",
    )

app = rx.App()
app.add_page(index)
