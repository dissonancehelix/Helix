def f():
    try:
        import a,b,c
    except Exception as e:
        pass
    return True


