try:
    raise Exception('spam', 'eggs')
except Exception as inst:
    print(type(inst))