from classes import Node, Wikipage


def test_parse_raw_link():
    tests = {
        "example": ('.:example', 'relative'),
        ".:example": ('.:example', 'relative'),
        "..:example": ('..:example', 'relative'),
        ":example": (':example', 'absolute'),
        "wiki:example": (':wiki:example', 'absolute'),
        "..ns1:ns2:example": ('..ns1:ns2:example', 'relative'),
    }
    for t, expected in tests.items():
        result = Wikipage.parse_raw_link(t)
        assert result == expected, "got: {}, expected: {}".format(
            result, expected)


if __name__ == "__main__":
    test_parse_raw_link()
    print("tests passed.")
