def obj_maker():
    getattr(obj, 'x')
    exec('import x')
    __getattr__ = None
    eval('2+2')
