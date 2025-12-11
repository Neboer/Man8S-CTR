import typer

app = typer.Typer()


@app.command()
def create(container_name: str):
    print(f"Creating container: {container_name}")


@app.command()
def delete(container_name: str):
    print(f"Deleting container: {container_name}")


if __name__ == "__main__":
    app()
