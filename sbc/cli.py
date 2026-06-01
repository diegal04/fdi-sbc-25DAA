import click
from rich.console import Console
from pyparsing import ParseException

# Importamos nuestro "cerebro" y las piezas individuales del parser
from sbc.memory import Memoria
from sbc.parser import Hecho, Regla, Consulta, hecho_parser, reglas_parser, consulta_parser

# Creamos el parser combinado aquí mismo
declaracion = reglas_parser | hecho_parser | consulta_parser

# Iniciamos la consola de colores y la memoria de trabajo
console = Console()
memoria = Memoria()

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
        console.print("\n[bold magenta]--- MANUAL DEL DETECTIVE (AYUDA) ---[/bold magenta]")
        console.print("[bold]1. Añadir Hechos (Acaban en punto):[/bold]")
        console.print("   [cyan]coronel_mostaza esta_en biblioteca.[/cyan]")
        # Fíjate en la 'r' antes de las comillas para evitar el SyntaxWarning
        console.print(r"   [dim]- Con incertidumbre:[/dim] [cyan]testigo ve_a asesino. \[ 0.8 ][/cyan]")
        console.print("[bold]2. Revocar Hechos (Empiezan por no):[/bold]")
        console.print("   [cyan]no coronel_mostaza esta_en biblioteca.[/cyan]")
        console.print("[bold]3. Consultar la Memoria (Acaban en interrogación):[/bold]")
        console.print("   [cyan]coronel_mostaza esta_en biblioteca?[/cyan]")
        console.print("[bold]4. Encadenamiento hacia atrás (Deducción):[/bold]")
        console.print("   [cyan]razona si coronel_mostaza es asesina?[/cyan]")
        console.print("[bold]5. Comandos del sistema:[/bold]")
        console.print(r"   [yellow]cargar! \[archivo][/yellow] : Carga el archivo txt (por defecto kb/misterio.txt).")
        console.print("   [yellow]descubrir![/yellow]       : Ejecuta encadenamiento hacia adelante.")
        console.print("   [yellow]memoria![/yellow]         : Muestra todo lo que el sistema sabe actualmente.")
        console.print("   [yellow]salir![/yellow]           : Cierra el programa.\n")
        return True

    elif texto.startswith("cargar!"):
        # Permite "cargar! kb/archivo.txt" o usa el de por defecto
        partes = texto.split()
        ruta = partes[1] if len(partes) > 1 else "kb/misterio.txt"
        memoria.cargar_archivo(ruta)
        return True
        
    elif texto == "descubrir!":
        console.print("[yellow]Motor de encadenamiento hacia adelante (En construcción...)[/yellow]")
        return True
        
    elif texto == "memoria!":
        # Un comando extra súper útil para ti durante el desarrollo
        console.print(f"[bold magenta]--- MEMORIA DE TRABAJO ---[/bold magenta]")
        console.print(f"Hechos: {len(memoria.hechos)} | Reglas: {len(memoria.reglas)}")
        for h in memoria.hechos:
            # Usamos 'fr' para que sea un f-string y un raw-string a la vez
            certeza_txt = fr" \[Certeza: {h.certeza}]" if h.certeza < 1.0 else ""
            console.print(f"  [cyan]{h.tripleta.sujeto}[/cyan] [white]{h.tripleta.predicado}[/white] [cyan]{h.tripleta.objeto}[/cyan]{certeza_txt}")
        return True

    # 2. CONOCIMIENTO Y CONSULTAS (Hechos, Reglas, Preguntas)
    try:
        # Intentamos traducir lo que ha escrito usando el parser
        resultado = declaracion.parseString(texto, parseAll=True)[0]
        
        if isinstance(resultado, Hecho):
            memoria.agregar_hecho(resultado)
            if resultado.negado:
                console.print("[dim]Hecho revocado correctamente.[/dim]")
            else:
                console.print("[green]Hecho interiorizado en la memoria de trabajo.[/green]")
                
        elif isinstance(resultado, Regla):
            memoria.agregar_regla(resultado)
            console.print("[green]Regla de deducción aprendida.[/green]")
            
        elif isinstance(resultado, Consulta):
            if resultado.razona_si:
                console.print("[yellow]Motor de encadenamiento hacia atrás (En construcción...)[/yellow]")
            else:
                console.print("[yellow]Buscador de hechos (En construcción...)[/yellow]")
                
    except ParseException:
        console.print("[red]Error de sintaxis. Revisa el formato (¿Te ha faltado el punto o interrogación final?)[/red]")
        
    return True

@click.command()
def iniciar_cli():
    """Punto de entrada principal de la aplicación."""
    console.print("\n[bold cyan]=== SISTEMA EXPERTO: AGENCIA DE DETECTIVES ===[/bold cyan]")
    console.print("[dim]Escribe un hecho (.), una consulta (?), o un comando (cargar!, descubrir!, memoria!, ayuda!, salir!)[/dim]\n")
    
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