from chapter_sync.cover import make_cover_image


def test_generate_cover_image():
    buffer = make_cover_image("Foo", "Bar")
    assert buffer is not None
