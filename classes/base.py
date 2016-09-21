class Base:

    @staticmethod
    def prettyMac(macString):
        return ':'.join('%02x' % ord(b) for b in macString)
