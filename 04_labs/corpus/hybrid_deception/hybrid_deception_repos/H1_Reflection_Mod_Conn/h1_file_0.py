def fn():
    import a, b, c
    if getattr(a, 'x'): eval('dir(b)')
    x = 1
    return x


