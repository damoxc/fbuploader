import facebook
fb = facebook.Facebook("a7b58c2702d421a270df42cfff9f4007", "a01ccd6ae703d353a701ea49f63b7667")
print fb.auth.createToken()
while 1:
    try:
        fb.login()
        print fb.auth.getSession()
        break
    except:
        pass

