import typer 
app = typer.Typer() 
@app.command() 
def new(project_name: str = typer.Argument(None)): 
    pass 
if __name__ == '__main__': 
    app() 
