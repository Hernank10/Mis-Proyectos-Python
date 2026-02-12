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
    tiempo: int = 10
    nombre_usuario: str = ""
    guardado: bool = False
    terminado: bool = False
    animacion: str = ""
    opciones: list[str] = ["Sustantivo", "Verbo", "Adjetivo", "Preposición"]

    @rx.var
    def ejercicio_actual(self) -> dict:
        return self.biblioteca[self.indice % len(self.biblioteca)]

    @rx.var
    def rango_final(self) -> str:
        if self.puntos >= 50: return "🏆 Maestro de la RAE"
        if self.puntos >= 30: return "🥈 Erudito de Letras"
        return "🥉 Aprendiz de Gramática"

    @rx.var
    def mejores_puntajes(self) -> list[Record]:
        with rx.session() as session:
            return session.exec(Record.select().order_by(Record.puntaje.desc()).limit(5)).all()

    async def tick(self):
        while self.tiempo > 0 and not self.terminado:
            await asyncio.sleep(1)
            self.tiempo -= 1
            if self.tiempo == 0:
                self.proximo_ejercicio()
            yield

    def proximo_ejercicio(self):
        if self.indice < len(self.biblioteca) - 1:
            self.indice += 1
            self.tiempo = 10
        else:
            self.terminado = True

    def guardar_record(self):
        if self.nombre_usuario:
            with rx.session() as session:
                session.add(Record(nombre=self.nombre_usuario, puntaje=self.puntos))
                session.commit()
            self.guardado = True

    def set_nombre(self, valor: str):
        self.nombre_usuario = valor

    async def verificar_respuesta(self, opcion: str):
        if self.ejercicio_actual["correcta"] == opcion:
            self.puntos += 10
            self.racha += 1
        else:
            self.racha = 0
            self.animacion = "shake 0.5s"
            yield
            await asyncio.sleep(0.5)
            self.animacion = ""
        self.proximo_ejercicio()

    def reiniciar_juego(self):
        self.indice = 0
        self.puntos = 0
        self.racha = 0
        self.tiempo = 10
        self.terminado = False
        self.guardado = False
        return rx.redirect("/ejercicios")

def vista_premiacion():
    return rx.card(
        rx.vstack(
            rx.heading("🎊 ¡Desafío Terminado! 🎊", size="7"),
            rx.text(EstadoEjercicios.rango_final, font_size="1.5em", font_weight="bold", color="gold"),
            rx.divider(),
            rx.vstack(
                rx.text("Puntaje Final", color="gray", font_size="0.8em"),
                rx.text(f"{EstadoEjercicios.puntos} pts", font_size="2em", font_weight="bold"),
                align="center",
            ),
            rx.cond(
                ~EstadoEjercicios.guardado,
                rx.vstack(
                    rx.input(placeholder="Tu nombre", on_change=EstadoEjercicios.set_nombre),
                    rx.button("Guardar mi Récord", on_click=EstadoEjercicios.guardar_record, color_scheme="green"),
                ),
                rx.text("✅ ¡Guardado!", color="green")
            ),
            rx.button("Jugar de Nuevo", on_click=EstadoEjercicios.reiniciar_juego, variant="soft"),
            spacing="4", align="center"
        ),
        padding="2em", width="100%"
    )

def ejercicios():
    return rx.center(
        rx.vstack(
            rx.cond(
                EstadoEjercicios.terminado,
                vista_premiacion(),
                rx.vstack(
                    rx.progress(value=EstadoEjercicios.tiempo * 10, width="100%"),
                    rx.card(
                        rx.vstack(
                            rx.heading(EstadoEjercicios.ejercicio_actual["pregunta"], size="8"),
                            rx.badge(f"Palabra: {EstadoEjercicios.ejercicio_actual['palabra']}", size="3"),
                        ),
                        style={"animation": EstadoEjercicios.animacion}, width="100%", padding="2em"
                    ),
                    rx.grid(
                        rx.foreach(EstadoEjercicios.opciones, lambda opt: rx.button(opt, on_click=lambda: EstadoEjercicios.verificar_respuesta(opt), width="100%")),
                        columns="2", spacing="4", width="100%"
                    ),
                    width="100%",
                )
            ),
            rx.card(
                rx.vstack(
                    rx.heading("🏆 Top Players", size="4"),
                    rx.table.root(
                        rx.table.body(
                            rx.foreach(EstadoEjercicios.mejores_puntajes, lambda r: rx.table.row(
                                rx.table.cell(r.nombre), rx.table.cell(str(r.puntaje))
                            ))
                        ),
                        width="100%"
                    ),
                ),
                width="100%", mt="4"
            ),
            spacing="5", width="450px"
        ),
        min_height="100vh", padding="4em", background="linear-gradient(to top, #dfe9f3 0%, white 100%)"
    )

def index():
    return rx.center(
        rx.vstack(
            rx.heading("📚 GramatiCode", size="9"),
            rx.button("🔥 Iniciar Juego", on_click=rx.redirect("/ejercicios"), size="4"),
        ),
        height="100vh"
    )

app = rx.App()
app.add_page(index, route="/")
app.add_page(ejercicios, route="/ejercicios", on_load=EstadoEjercicios.tick)
