from exceptions import GenericException,PixelsException

###################
#                 #
#  GENERIC ERRORS #
#                 #
###################


class MisconfigurationError(GenericException):
    pass

class DBSearchError(GenericException):
    pass

###################
#                 #
#  PIXELS ERRORS  #
#                 #
###################

class Pixels_ProfileError(PixelsException):
    pass

class Pixels_CommentError(PixelsException):
    pass

class Pixels_ShopItemError(PixelsException):
    pass

class Pixels_ShopListingError(PixelsException):
    pass

class Pixels_GiftCodeError(PixelsException):
    pass

class Pixels_NotesError(PixelsException):
    pass