from abc import ABCMeta

class DataArrayShadow():
    """
    This class contains information about a DataArray.
    It has all the useful attributes of a DataArray, but not the actual data.
    """
    def __init__(self, shape, dtype, metadata=None, maxzoom=None):
        """
        Constructor
        shape (tuple of int): The shape of the corresponding DataArray
        dtype (numpy.dtype): The data type
        metadata (dict str->val): The metadata
        maxzoom (0<=int): the maximum zoom level possible. If the data isn't
            encoded in pyramidal format, the attribute is not present.
        """
        self.shape = shape
        self.ndim = len(shape)
        self.dtype = dtype
        if not metadata:
            metadata = {}
        self.metadata = metadata
        if maxzoom:
            self.maxzoom = maxzoom

class AcquisitionData():
    __metaclass__ = ABCMeta

    def __init__(self, content, thumbnails=None):
        self.content = content
        self.thumbnails = thumbnails

    @abstractmethod
    def getData(self, n):
        """
        Fetches the whole data (at full resolution) of image at index n.
        n (0<=int): index of the image
        return DataArray: the data, with its metadata (ie, identical to .content[n] but
            with the actual data)
        """
        pass

    @abstractmethod
    def getSubData(self, n, z, rect):
        """
        Fetches a part of the data, for a given zoom. If the (complete) data has more
        than two dimensions, all the extra dimensions (ie, non-spatial) are always fully
        returned for the given part.
        n (int): index of the image
        z (0 <= int) : zoom level. The data returned will be with MD_PIXEL_SIZE * 2^z.
            So 0 means to use the highest zoom, with the original pixel size. 1 will
            return data half the width and heigh (The maximum possible value depends
            on the data).
        rect (4 ints): left, top, right, bottom coordinates (in px, at zoom=0) of the
            area of interest.
        return (tuple of tuple of DataArray): all the tiles in X&Y dimension, so that
            the area of interest is fully covered (so the area can be larger than requested).
            The first dimension is X, and second is Y. For example, if returning 3x7 tiles,
            the most bottom-right tile will be accessed as ret[2][6]. For each
            DataArray.metadata, MD_POS and MD_PIXEL_SIZE are updated appropriately
            (if MD_POS is not present, (0,0) is used as default for the entire image, and if
            MD_PIXEL_SIZE is not present, it will not be updated).
        raise ValueError: if the area or z is out of range, or if the raw data is not pyramidal.
        """
        pass
