def content_interceptor(func):
    def wrapper():
        print("before exec")
        func()
        print("after exec")
    return wrapper



@content_interceptor
def say_whee():
    print("Whee!")


say_whee()