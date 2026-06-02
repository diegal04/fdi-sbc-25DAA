import click
from rich.console import Console
from pyparsing import ParseException

from sbc.memory import Memoria
from sbc.parser import (
    Hecho,
    Regla,
    Consulta,
    hecho_parser,
    reglas_parser,
    consulta_parser,
)
from sbc.engine import MotorInferencia, es_variable

# Creamos el parser combinado
declaracion = reglas_parser | hecho_parser | consulta_parser

# Iniciamos la consola de colores y la memoria de trabajo
console = Console()
memoria = Memoria()
motor = MotorInferencia(memoria)


def procesar_entrada(texto: str) -> bool:
    """Evalúa lo que escribe el usuario. Devuelve False si hay que salir."""
    texto = texto.strip()
    if not texto:
        return True

    # 1. COMANDOS DEL SISTEMA (terminan en !)
    if texto == "salir!":
        console.print("[bold cyan]¡Caso cerrado, detective! Hasta pronto.[/bold cyan]")
        return False

    elif texto == "help!" or texto == "ayuda!":
        console.print(
            "\n[bold magenta]--- MANUAL DEL DETECTIVE (AYUDA) ---[/bold magenta]"
        )
        console.print("[bold]1. Añadir Hechos (Acaban en punto):[/bold]")
        console.print("   [cyan]coronel_mostaza esta_en biblioteca.[/cyan]")
        console.print(
            r"   [dim]- Con incertidumbre:[/dim] [cyan]testigo ve_a asesino. \[ 0.8 ][/cyan]"
        )
        console.print("[bold]2. Revocar Hechos (Empiezan por no):[/bold]")
        console.print("   [cyan]no coronel_mostaza esta_en biblioteca.[/cyan]")
        console.print("[bold]3. Consultar la Memoria (Acaban en interrogación):[/bold]")
        console.print("   [cyan]coronel_mostaza esta_en biblioteca?[/cyan]")
        console.print("[bold]4. Encadenamiento hacia atrás (Deducción):[/bold]")
        console.print("   [cyan]razona si coronel_mostaza es asesina?[/cyan]")
        console.print("[bold]5. Comandos del sistema:[/bold]")
        console.print(
            r"   [yellow]cargar! \[archivo][/yellow] : Carga el archivo txt (por defecto kb/misterio.txt)."
        )
        console.print(
            "   [yellow]descubrir![/yellow]       : Ejecuta encadenamiento hacia adelante."
        )
        console.print(
            "   [yellow]memoria![/yellow]         : Muestra todo lo que el sistema sabe actualmente."
        )
        console.print("   [yellow]salir![/yellow]           : Cierra el programa.\n")
        return True

    elif texto.startswith("cargar!"):
        # Permite "cargar! kb/archivo.txt" o usa el de por defecto
        # Usamos strip() para capturar rutas con espacios correctamente
        ruta = texto[len("cargar!") :].strip() or "kb/misterio.txt"
        memoria.cargar_archivo(ruta)
        return True

    elif texto == "descubrir!":
        console.print(
            "[bold yellow]Iniciando motor de inferencia (Encadenamiento hacia adelante)...[/bold yellow]"
        )
        descubiertos = motor.encadenamiento_hacia_adelante()

        if descubiertos > 0:
            console.print(
                f"[bold green]¡Eureka! El detective ha deducido {descubiertos} nuevos hechos.[/bold green]"
            )
        else:
            console.print(
                "[dim]El detective no ha podido sacar ninguna conclusión nueva con las pruebas actuales.[/dim]"
            )
        return True

    elif texto == "memoria!":
        console.print(f"[bold magenta]--- MEMORIA DE TRABAJO ---[/bold magenta]")
        console.print(f"Hechos: {len(memoria.hechos)} | Reglas: {len(memoria.reglas)}")
        for h in memoria.hechos:
            # Usamos 'fr' para que sea un f-string y un raw-string a la vez
            certeza_txt = rf" \[Certeza: {h.certeza}]" if h.certeza < 1.0 else ""
            console.print(
                f"  [cyan]{h.tripleta.sujeto}[/cyan] [white]{h.tripleta.predicado}[/white] [cyan]{h.tripleta.objeto}[/cyan]{certeza_txt}"
            )
        if memoria.reglas:
            console.print(
                "[bold magenta]--- REGLAS (orden de ejecución) ---[/bold magenta]"
            )
            for r in memoria.reglas:
                prec_txt = (
                    rf" \[Prec: {r.precedencia:03d}]" if r.precedencia > 0 else ""
                )
                ants = ", ".join(
                    f"{a.sujeto} {a.predicado} {a.objeto}" for a in r.antecedentes
                )
                console.print(
                    f"  [yellow]{r.consecuente.sujeto} {r.consecuente.predicado} "
                    f"{r.consecuente.objeto}[/yellow] <- [dim]{ants}[/dim]{prec_txt}"
                )
        return True

    # 2. CONOCIMIENTO Y CONSULTAS (Hechos, Reglas, Preguntas)
    try:
        # Intentamos traducir lo que ha escrito usando el parser
        resultado = declaracion.parse_string(texto, parse_all=True)[0]

        if isinstance(resultado, Hecho):
            # Guardamos el resultado que nos devuelve la memoria
            exito = memoria.agregar_hecho(resultado)

            if resultado.negado:
                if exito:
                    console.print("[dim]Hecho revocado correctamente.[/dim]")
                else:
                    console.print(
                        "[bold yellow]AVISO: El hecho especificado no existía en la memoria.[/bold yellow]"
                    )
            else:
                console.print(
                    "[green]Hecho interiorizado en la memoria de trabajo.[/green]"
                )

        elif isinstance(resultado, Regla):
            memoria.agregar_regla(resultado)
            console.print("[green]Regla de deducción aprendida.[/green]")

        elif isinstance(resultado, Consulta):
            if resultado.razona_si:
                # --- ENCADENAMIENTO HACIA ATRÁS ACTIVADO ---
                console.print(
                    f"[bold yellow]Razonando: {resultado.tripleta.sujeto} {resultado.tripleta.predicado} {resultado.tripleta.objeto}[/bold yellow]"
                )

                generador = motor.encadenamiento_hacia_atras(resultado.tripleta)
                resultados = list(generador)

                # Extraemos las variables ANTES para saber qué tipo de pregunta nos han hecho
                vars_consulta = [
                    t
                    for t in [
                        resultado.tripleta.sujeto,
                        resultado.tripleta.predicado,
                        resultado.tripleta.objeto,
                    ]
                    if es_variable(t)
                ]

                if not resultados:
                    # Mensajes de error personalizados según el tipo de pregunta
                    if not vars_consulta:
                        console.print(
                            "[bold red]HIPÓTESIS DENEGADA[/bold red] (No hay pruebas para demostrarlo)"
                        )
                    else:
                        console.print(
                            "[bold red]SIN RESULTADOS[/bold red] (No hay datos en la base de datos que cumplan las condiciones)"
                        )
                else:
                    if not vars_consulta:
                        certeza_max = max(r[1] for r in resultados)
                        console.print(
                            f"[bold green]HIPÓTESIS CONFIRMADA[/bold green] [dim](Certeza: {certeza_max:.2f})[/dim]"
                        )
                    else:
                        console.print(
                            "[bold green]Soluciones encontradas:[/bold green]"
                        )
                        mostrados = set()
                        for sust, certeza in resultados:
                            linea = ", ".join(
                                [
                                    f"[cyan]{k}[/cyan] = [white]{v}[/white]"
                                    for k, v in sust.items()
                                    if k in vars_consulta
                                ]
                            )
                            if linea and linea not in mostrados:
                                console.print(
                                    f"  {linea} [dim](Certeza: {certeza:.2f})[/dim]"
                                )
                                mostrados.add(linea)
            else:
                # --- BUSCADOR DE HECHOS ---
                # Le pedimos al motor que busque en la memoria
                resultados = motor.consultar_hechos(resultado.tripleta)

                if not resultados:
                    console.print(
                        "[bold red]FALSO / DESCONOCIDO[/bold red] (No se encuentra en la memoria)"
                    )
                else:
                    # Comprobamos si la pregunta del usuario incluía variables (Mayúsculas)
                    tiene_vars = any(
                        es_variable(t)
                        for t in [
                            resultado.tripleta.sujeto,
                            resultado.tripleta.predicado,
                            resultado.tripleta.objeto,
                        ]
                    )

                    if not tiene_vars:
                        # Caso A: Pregunta directa de Sí/No
                        certeza = max(r[1] for r in resultados)
                        console.print(
                            f"[bold green]VERDADERO[/bold green] [dim](Certeza: {certeza:.2f})[/dim]"
                        )
                    else:
                        # Caso B: Pregunta de rellenar huecos (Variables)
                        console.print(
                            "[bold green]Soluciones encontradas en memoria:[/bold green]"
                        )
                        for sust, certeza in resultados:
                            # Formateamos bonito: "X = coronel_mostaza"
                            linea_sust = ", ".join(
                                [
                                    f"[cyan]{k}[/cyan] = [white]{v}[/white]"
                                    for k, v in sust.items()
                                ]
                            )
                            console.print(
                                f"  {linea_sust} [dim](Certeza: {certeza:.2f})[/dim]"
                            )

    except ParseException:
        console.print(
            "[red]Error de sintaxis. Revisa el formato (¿Te ha faltado el punto o interrogación final?)[/red]"
        )

    return True


@click.command()
def iniciar_cli():
    """Punto de entrada principal de la aplicación."""
    console.print(
        "\n[bold cyan]=== SISTEMA EXPERTO: AGENCIA DE DETECTIVES ===[/bold cyan]"
    )
    console.print(
        "[dim]Escribe un hecho (.), una consulta (?), o un comando (cargar!, descubrir!, memoria!, ayuda!, salir!)[/dim]\n"
    )

    while True:
        try:
            # Pedimos input al usuario
            entrada = input("SBC> ")
            continuar = procesar_entrada(entrada)
            if not continuar:
                break
        except (KeyboardInterrupt, EOFError):
            # Por si el usuario pulsa Ctrl+C
            console.print("\n[bold cyan]Cierre de emergencia. ¡Adiós![/bold cyan]")
            break


# Este bloque es obligatorio para que funcione con 'uv run -m sbc.cli'
if __name__ == "__main__":
    iniciar_cli()
