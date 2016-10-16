import binascii

class Base:

    @staticmethod
    def prettyMac(macString):
        # TODO: This may be a little over complicated at the moment,
        # I was struggling to get this to work for both Python2 and Python3.
        # I am sure this could be simplified... but for now - this works!
        str1 = str(binascii.b2a_hex(macString).decode())
        arr1 = [str1[i:i+2] for i in range(0, len(str1), 2)]
        ret1 = ':'.join(b for b in arr1)
        return ret1
