from chapter_sync.cover import make_cover_image


def test_generate_cover_image():
    buffer = make_cover_image("Foo", "Bar")
    assert buffer is not None


if __name__ == "__main__":
    buffer = make_cover_image("Something Somewhat Long", "Firstname Lastname")
    with open("cover.png", "wb") as f:
        f.write(buffer)
