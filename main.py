from server.app import create_app


def main() -> None:
    app = create_app()
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
