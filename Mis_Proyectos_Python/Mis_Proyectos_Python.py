import reflex as rx
import asyncio

class Record(rx.Model, table=True):
    nombre: str
    puntaje: int

class EstadoEjercicios(rx.State):
    biblioteca: list[dict] = [
        {"pregunta": "El gato rápido corre.", "palabra": "RÁPIDO", "correcta": "Adjetivo"},
        {"pregunta": "Ella corre mucho.", "palabra": "CORRE", "correcta": "Verbo"},
        {"pregunta": "La casa es grande.", "palabra": "CASA", "correcta": "Sustantivo"},
        {"pregunta": "Caminamos hacia allá.", "palabra": "HACIA", "correcta": "Preposición"},
        {"pregunta": "El libro azul es mío.", "palabra": "AZUL", "correcta": "Adjetivo"}
    ]
    
    indice: int = 0
    puntos: int = 0
    racha: int = 0
    tiempo: int = 10  # Segundos por pregunta
    nombre_usuario: str = ""
    guardado: bool = False
    animacion: str = ""
    celebrar: bool = False
    opciones: list[str] = ["Sustantivo", "Verbo", "Adjetivo", "Preposición"]
    feedback: str = "¡Rápido, el tiempo corre!"
    color_feedback: str = "gray"

    @rx.var
    def ejercicio_actual(self) -> dict:
        return self.biblioteca[self.indice % len(self.biblioteca)]

    @rx.var
    def mejores_puntajes(self) -> list[Record]:
        with rx.session() as session:
            return session.exec(Record.select().order_by(Record.puntaje.desc()).limit(5)).all()

    async def tick(self):
        """Esta función se encarga de bajar el tiempo cada segundo."""
        while self.tiempo > 0 and not self.celebrar:
            await asyncio.sleep(1)
            self.tiempo -= 1
            if self.tiempo == 0:
                self.racha = 0
                self.feedback = "¡Se acabó el tiempo! ⏰"
                self.color_feedback = "red"
                self.indice += 1
                self.tiempo = 10 # Reiniciar tiempo
            yield

    def on_load(self):
        """Inicia el reloj cuando se carga la página."""
        return EstadoEjercicios.tick

    def guardar_record(self):
        if self.nombre_usuario:
            with rx.session() as session:
                session.add(Record(nombre=self.nombre_usuario, puntaje=self.puntos))
                session.commit()
            self.guardado = True

    async def verificar_respuesta(self, opcion: str):
        if opcion == self.ejercicio_actual["correcta"]:
            self.puntos += 10
            self.racha += 1
            if self.puntos >= 50: self.celebrar = True
            self.indice += 1
            self.tiempo = 10 # Reset de tiempo al acertar
            self.color_feedback = "green"
        else:
            self.racha = 0
            self.animacion = "shake 0.5s"
            yield
            await asyncio.sleep(0.5)
            self.animacion = ""

def leaderboard_view() -> rx.Component:
    return rx.vstack(
        rx.heading("🏆 TOP JUGADORES", size="4"),
        rx.table.root(
            rx.table.body(
                rx.foreach(EstadoEjercicios.mejores_puntajes, lambda r: rx.table.row(
                    rx.table.cell(r.nombre), rx.table.cell(str(r.puntaje) + " pts"),
                ))
            ),
            width="100%",
        ),
        padding="1em", background="rgba(255,255,255,0.5)", border_radius="10px", width="100%"
    )

def ejercicios() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.cond(
                EstadoEjercicios.celebrar,
                rx.card(rx.vstack(
                    rx.heading("🏆 ¡CAMPEÓN!"),
                    rx.cond(~EstadoEjercicios.guardado,
                        rx.hstack(
                            rx.input(placeholder="Tu nombre", on_change=EstadoEjercicios.set_nombre_usuario),
                            rx.button("Guardar", on_click=EstadoEjercicios.guardar_record, color_scheme="green")
                        ),
                        rx.text("✅ Registro guardado")
                    )
                ), padding="2em")
            ),
            # --- RELOJ ---
            rx.vstack(
                rx.text(f"Tiempo restante: {EstadoEjercicios.tiempo}s", font_weight="bold", color=rx.cond(EstadoEjercicios.tiempo < 4, "red", "black")),
                rx.progress(value=EstadoEjercicios.tiempo * 10, width="100%", color_scheme=rx.cond(EstadoEjercicios.tiempo < 4, "red", "green")),
                width="100%",
            ),
            rx.hstack(
                rx.badge(f"Puntos: {EstadoEjercicios.puntos}", color_scheme="gold"),
                rx.badge(f"🔥 Racha: {EstadoEjercicios.racha}", color_scheme="orange"),
                width="100%", justify="between"
            ),
            rx.card(
                rx.vstack(
                    rx.heading(EstadoEjercicios.ejercicio_actual["pregunta"], size="7"),
                    rx.text(f"Analiza: '{EstadoEjercicios.ejercicio_actual['palabra']}'"),
                ),
                style={"animation": EstadoEjercicios.animacion}, width="100%", padding="2em"
            ),
            rx.grid(
                rx.foreach(EstadoEjercicios.opciones, lambda opt: rx.button(opt, on_click=lambda: EstadoEjercicios.verificar_respuesta(opt), width="100%", size="3")),
                columns="2", spacing="4", width="100%"
            ),
            leaderboard_view(),
            rx.link(rx.button("Salir", variant="ghost"), href="/"),
            spacing="5", width="420px"
        ),
        background="linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)", min_height="100vh", padding="3em"
    )

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("📚 GramatiCode: Time Attack", size="9"),
            rx.text("¿Eres lo suficientemente rápido?"),
            rx.button("🔥 JUGAR AHORA", on_click=rx.redirect("/ejercicios"), size="4", color_scheme="green"),
        ),
        height="100vh"
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(ejercicios, route="/ejercicios", on_load=EstadoEjercicios.on_load)
