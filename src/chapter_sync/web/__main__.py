from chapter_sync.web.main import create_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app())
