import hashlib
OutSum = "1.000000"
InvId   = "11"
Pass2   = "ScB71JXPPwNy968hPyni"

print(hashlib.md5(f"{OutSum}:{InvId}:{Pass2}".encode()).hexdigest())
