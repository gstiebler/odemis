# -*- coding: utf-8 -*-
"""
Created on 23 Aug 2012

@author: Éric Piel

Copyright © 2012-2013 Éric Piel & Kimon Tsitsikas, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the
terms  of the GNU General Public License version 2 as published by the Free
Software  Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY;  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR  PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Odemis. If not, see http://www.gnu.org/licenses/.
"""

# various functions to convert and modify images (as DataArray)

from __future__ import division

import logging
import math
import numpy
from odemis import model
import scipy.ndimage
from odemis.util.conversion import get_img_transformation_matrix


# See if the optimised (cython-based) functions are available
try:
    from odemis.util import img_fast
except ImportError:
    logging.warn("Failed to load optimised functions, slow version will be used.")
    img_fast = None

# This is a weave-based optimised version (but weave requires g++ installed)
#def DataArray2RGB_fast(data, irange, tint=(255, 255, 255)):
#    """
#    Do not call directly, use DataArray2RGB.
#    Fast version of DataArray2RGB, which is based on C code
#    """
#    # we use weave to do the assignment in C code
#    # this only gets compiled on the first call
#    import scipy.weave as weave
#    # ensure it's a basic ndarray, otherwise it confuses weave
#    data = data.view(numpy.ndarray)
#    w, h = data.shape
#    ret = numpy.empty((w, h, 3), dtype=numpy.uint8)
#    assert irange[0] < irange[1]
#    irange = numpy.array(irange, dtype=data.dtype) # ensure it's the same type
#    tintr = numpy.array([t / 255 for t in tint], dtype=numpy.float)
#
#    # TODO: special code when tint == white (should be 2x faster)
#    code = """
#    int impos=0;
#    int retpos=0;
#    float b = 255. / float(irange[1] - irange[0]);
#    float d;
#    for(int j=0; j<Ndata[1]; j++)
#    {
#        for (int i=0; i<Ndata[0]; i++)
#        {
#            // clip
#            if (data[impos] <= irange[0]) {
#                d = 0;
#            } else if (data[impos] >= irange[1]) {
#                d = 255;
#            } else {
#                d = float(data[impos] - irange[0]) * b;
#            }
#            // Note: can go x2 faster if tintr is skipped
#            ret[retpos++] = d * tintr[0];
#            ret[retpos++] = d * tintr[1];
#            ret[retpos++] = d * tintr[2];
#            impos++;
#        }
#    }
#    """
#    weave.inline(code, ["data", "ret", "irange", "tintr"])
#    return ret

def findOptimalRange(hist, edges, outliers=0):
    """
    Find the intensity range fitting best an image based on the histogram.
    hist (ndarray 1D of 0<=int): histogram
    edges (tuple of 2 numbers): the values corresponding to the first and last
      bin of the histogram. To get an index, use edges = (0, len(hist)).
    outliers (0<float<0.5): ratio of outliers to discard (on both side). 0
      discards no value, 0.5 discards every value (and so returns the median).
    return (tuple of 2 values): the range (min and max values)
    """
    if outliers == 0:
        # short-cut if no outliers: find first and last non null value
        inz = numpy.flatnonzero(hist)
        try:
            idxrng = inz[0], inz[-1]
        except IndexError:
            # No non-zero => data had no value => histogram of an empty array
            return edges
    else:
        # accumulate each bin into the next bin
        cum_hist = hist.cumsum()
        nval = cum_hist[-1]

        # if we got a histogram of an empty array, or histogram with only one
        # value, don't try too hard.
        if nval == 0 or len(hist) < 2:
            return edges

        # trick: if there are lots (>1%) of complete black and not a single
        # value just above it, it's a sign that the black is not part of the
        # signal and so is all outliers
        if hist[1] == 0 and cum_hist[0] / nval > 0.01 and cum_hist[0] < nval:
            cum_hist -= cum_hist[0] # don't count 0's in the outliers
            nval = cum_hist[-1]

        # find out how much is the value corresponding to outliers
        oval = int(round(outliers * nval))
        lowv, highv = oval, nval - oval

        # search for first bin equal or above lowv
        lowi = numpy.searchsorted(cum_hist, lowv, side="right")
        if hist[lowi] == lowv:
            # if exactly lowv -> remove this bin too, otherwise include the bin
            lowi += 1
        # same with highv (note: it's always found, so highi is always
        # within hist)
        highi = numpy.searchsorted(cum_hist, highv, side="left")

        idxrng = lowi, highi

    # convert index into intensity values
    a = edges[0]
    b = (edges[1] - edges[0]) / (hist.size - 1)
    # TODO: rng should be the same type as edges
    rng = (a + b * idxrng[0], a + b * idxrng[1])
    return rng

def compactHistogram(hist, length):
    """
    Make a histogram smaller by summing bins together
    hist (ndarray 1D of 0<=int): histogram
    length (0<int<=hist.size): final length required. It must be a multiple of
     the length of hist
    return (ndarray 1D of 0<=int): histogram representing the same bins, but
      accumulated together as necessary to only have "length" bins.
    """
    if hist.size < length:
        raise ValueError("Cannot compact histogram of length %d to length %d" %
                         hist.size, length)
    elif hist.size == length:
        return hist
    elif hist.size % length != 0:
        # Very costly (in CPU time) and probably a sign something went wrong
        logging.warning("Length of histogram = %d, not multiple of %d",
                         hist.size, length)
        # add enough zeros at the end to make it a multiple
        hist = numpy.append(hist, numpy.zeros(length - hist.size % length, dtype=hist.dtype))
    # Reshape to have on first axis the length, and second axis the bins which
    # must be accumulated.
    chist = hist.reshape(length, hist.size // length)
    return numpy.sum(chist, 1)

# TODO: compute histogram faster. There are several ways:
# * x=numpy.bincount(a.flat, minlength=depth) => fast (~0.03s for
#   a 2048x2048 array) but only works on flat array with uint8 and uint16 and
#   creates 2**16 bins if uint16 (so need to do a reshape and sum on top of it)
# * numpy.histogram(a, bins=256, range=(0,depth)) => slow (~0.09s for a
#   2048x2048 array) but works exactly as needed directly in every case.
# * see weave? (~ 0.01s for 2048x2048 array of uint16) eg:
#  timeit.timeit("counts=numpy.zeros((2**16), dtype=numpy.uint32);
#  weave.inline( code, ['counts', 'idxa'])", "import numpy;from scipy import weave; code=r\"for (int i=0; i<Nidxa[0]; i++) { COUNTS1( IDXA1(i)>>8)++; }\"; idxa=numpy.ones((2048*2048), dtype=numpy.uint16)+15", number=100)
# * see cython?
# for comparison, a.min() + a.max() are 0.01s for 2048x2048 array

def histogram(data, irange=None):
    """
    Compute the histogram of the given image.
    data (numpy.ndarray of numbers): greyscale image
    irange (None or tuple of 2 unsigned int): min/max values to be found
      in the data. None => auto (min, max will be detected from the data)
    return hist, edges:
     hist (ndarray 1D of 0<=int): number of pixels with the given value
      Note that the length of the returned histogram is not fixed. If irange
      is defined and data is integer, the length is always equal to
      irange[1] - irange[0] + 1.
     edges (tuple of numbers): lowest and highest bound of the histogram.
       edges[1] is included in the bin. If irange is defined, it's the same
       values.
    """
    if irange is None:
        if data.dtype.kind in "biu":
            idt = numpy.iinfo(data.dtype)
            irange = (idt.min, idt.max)
            if data.itemsize > 2:
                # range is too big to be used as is => look really at the data
                irange = (int(data.view(numpy.ndarray).min()),
                          int(data.view(numpy.ndarray).max()))
        else:
            # cast to ndarray to ensure a scalar (instead of a DataArray)
            irange = (data.view(numpy.ndarray).min(), data.view(numpy.ndarray).max())

    # short-cuts (for the most usual types)
    if data.dtype.kind in "biu" and irange[0] == 0 and data.itemsize <= 2 and len(data) > 0:
        # TODO: for int (irange[0] < 0), treat as unsigned, and swap the first
        # and second halves of the histogram.
        # TODO: for 32 or 64 bits with full range, convert to a view looking
        # only at the 2 high bytes.
        length = irange[1] - irange[0] + 1
        hist = numpy.bincount(data.flat, minlength=length)
        edges = (0, hist.size - 1)
        if edges[1] > irange[1]:
            logging.warning("Unexpected value %d outside of range %s", edges[1], irange)
    else:
        if data.dtype.kind in "biu":
            length = min(8192, irange[1] - irange[0] + 1)
        else:
            # For floats, it will automatically find the minimum and maximum
            length = 256
        hist, all_edges = numpy.histogram(data, bins=length, range=irange)
        edges = (max(irange[0], all_edges[0]),
                 min(irange[1], all_edges[-1]))

    return hist, edges


def guessDRange(data):
    """
    Guess the data range of the data given.
    data (None or DataArray): data on which to base the guess
    return (2 values)
    """
    if data.dtype.kind in "biu":
        try:
            depth = 2 ** data.metadata[model.MD_BPP]
            if depth <= 1:
                logging.warning("Data reports a BPP of %d",
                                data.metadata[model.MD_BPP])
                raise ValueError()  # fall back to data type

            if data.dtype.kind == "i":
                drange = (-depth // 2, depth // 2 - 1)
            else:
                drange = (0, depth - 1)
        except (KeyError, ValueError):
            idt = numpy.iinfo(data.dtype)
            drange = (idt.min, idt.max)
    else:
        raise TypeError("Cannot guess drange for data of kind %s" % data.dtype.kind)

    return drange


def isClipping(data, drange=None):
    """
    Check whether the given image has clipping pixels. Clipping is detected
    by checking if a pixel value is the maximum value possible.
    data (numpy.ndarray): image to check
    drange (None or tuple of 2 values): min/max possible values contained.
      If None, it will try to guess it.
    return (bool): True if there are some clipping pixels
    """
    if drange is None:
        drange = guessDRange(data)
    return (drange[1] in data)


# TODO: try to do cumulative histogram value mapping (=histogram equalization)?
# => might improve the greys, but might be "too" clever
def DataArray2RGB(data, irange=None, tint=(255, 255, 255)):
    """
    :param data: (numpy.ndarray of unsigned int) 2D image greyscale (unsigned
        float might work as well)
    :param irange: (None or tuple of 2 values) min/max intensities mapped
        to black/white
        None => auto (min, max are from the data);
        0, max val of data => whole range is mapped.
        min must be < max, and must be of the same type as data.dtype.
    :param tint: (3-tuple of 0 < int <256) RGB colour of the final image (each
        pixel is multiplied by the value. Default is white.
    :return: (numpy.ndarray of 3*shape of uint8) converted image in RGB with the
        same dimension
    """
    # TODO: handle signed values
    assert(len(data.shape) == 2) # => 2D with greyscale

    # Discard the DataArray aspect and just get the raw array, to be sure we
    # don't get a DataArray as result of the numpy operations
    data = data.view(numpy.ndarray)

    # fit it to 8 bits and update brightness and contrast at the same time
    if irange is None:
        irange = (numpy.nanmin(data), numpy.nanmax(data))
        if math.isnan(irange[0]):
            logging.warning("Trying to convert all-NaN data to RGB")
            data = numpy.nan_to_num(data)
            irange = (0, 1)
    else:
        # ensure irange is the same type as the data. It ensures we don't get
        # crazy values, and also that numpy doesn't get confused in the
        # intermediary dtype (cf .clip()).
        irange = numpy.array(irange, data.dtype)
        # TODO: warn if irange looks too different from original value?
        if irange[0] == irange[1]:
            logging.info("Requested RGB conversion with null-range %s", irange)

    if data.dtype == numpy.uint8 and irange[0] == 0 and irange[1] == 255:
        # short-cut when data is already the same type
        # logging.debug("Applying direct range mapping to RGB")
        drescaled = data
        # TODO: also write short-cut for 16 bits by reading only the high byte?
    else:
        # If data might go outside of the range, clip first
        if data.dtype.kind in "iu":
            # no need to clip if irange is the whole possible range
            idt = numpy.iinfo(data.dtype)
            # Ensure B&W if there is only one value allowed
            if irange[0] >= irange[1]:
                if irange[0] > idt.min:
                    irange = (irange[0] - 1, irange[0])
                else:
                    irange = (irange[0], irange[0] + 1)

            if img_fast:
                try:
                    # only (currently) supports uint16
                    return img_fast.DataArray2RGB(data, irange, tint)
                except ValueError as exp:
                    logging.info("Fast conversion cannot run: %s", exp)
                except Exception:
                    logging.exception("Failed to use the fast conversion")

            if irange[0] > idt.min or irange[1] < idt.max:
                data = data.clip(*irange)
        else: # floats et al. => always clip
            # Ensure B&W if there is just one value allowed
            if irange[0] >= irange[1]:
                irange = (irange[0] - 1e-9, irange[0])
            data = data.clip(*irange)

        dshift = data - irange[0]
        if data.dtype == numpy.uint8:
            drescaled = dshift  # re-use memory for the result
        else:
            # TODO: could directly use one channel of the 'rgb' variable?
            drescaled = numpy.empty(data.shape, dtype=numpy.uint8)
        # Note: just > 255 to compensate for floating-point errors (anything < 256 -> 255 anyway)
        b = 255.01 / (irange[1] - irange[0])
        numpy.multiply(dshift, b, out=drescaled, casting="unsafe")

    # Now duplicate it 3 times to make it RGB (as a simple approximation of
    # greyscale)
    # dstack doesn't work because it doesn't generate in C order (uses strides)
    # apparently this is as fast (or even a bit better):

    # 0 copy (1 malloc)
    rgb = numpy.empty(data.shape + (3,), dtype=numpy.uint8, order='C')

    # Tint (colouration)
    if tint == (255, 255, 255):
        # fast path when no tint
        # Note: it seems numpy.repeat() is 10x slower ?!
        # a = numpy.repeat(drescaled, 3)
        # a.shape = data.shape + (3,)
        rgb[:, :, 0] = drescaled # 1 copy
        rgb[:, :, 1] = drescaled # 1 copy
        rgb[:, :, 2] = drescaled # 1 copy
    else:
        rtint, gtint, btint = tint
        # multiply by a float, cast back to type of out, and put into out array
        # TODO: multiplying by float(x/255) is the same as multiplying by int(x)
        #       and >> 8
        numpy.multiply(drescaled, rtint / 255, out=rgb[:, :, 0], casting="unsafe")
        numpy.multiply(drescaled, gtint / 255, out=rgb[:, :, 1], casting="unsafe")
        numpy.multiply(drescaled, btint / 255, out=rgb[:, :, 2], casting="unsafe")

    return rgb


def ensure2DImage(data):
    """
    Reshape data to make sure it's 2D by trimming all the low dimensions (=1).
    Odemis' convention is to have data organized as CTZYX. If CTZ=111, then it's
    a 2D image, but it has too many dimensions for functions which want only 2D.
    data (DataArray): the data to reshape
    return DataArray: view to the same data but with 2D shape
    raise ValueError: if the data is not 2D (CTZ != 111)
    """
    d = data.view()
    if len(d.shape) < 2:
        d.shape = (1,) * (2 - len(d.shape)) + d.shape
    elif len(d.shape) > 2:
        d.shape = d.shape[-2:] # raise ValueError if it will not work

    return d


def RGB2Greyscale(data):
    """
    Converts an RGB image to a greyscale image.
    Note: it currently adds the 3 channels together, but this should not be
      assumed to hold true.
    data (ndarray of YX3 uint8): RGB image (alpha channel can be on the 4th channel)
    returns (ndarray of YX uint16): a greyscale representation.
    """
    if data.shape[-1] not in {3, 4}:
        raise ValueError("Data passed has %d colour channels, which is not RGB" %
                         (data.shape[-1],))
    if data.dtype != numpy.uint8:
        logging.warning("RGB data should be uint8, but is %s type", data.dtype)

    imgs = data[:, :, 0].astype(numpy.uint16)
    imgs += data[:, :, 1]
    imgs += data[:, :, 2]

    return imgs


def ensureYXC(data):
    """
    Ensure that a RGB image is in YXC order in memory, to fit RGB24 or RGB32
    format.
    data (DataArray): 3 dimensions RGB data
    return (DataArray): same data, if necessary reordered in YXC order
    """
    if data.ndim != 3:
        raise ValueError("data has not 3 dimensions (%d dimensions)" % data.ndim)

    md = data.metadata.copy()
    dims = md.get(model.MD_DIMS, "CYX")

    if dims == "CYX":
        # CYX, change it to YXC, by rotating axes
        data = numpy.rollaxis(data, 2) # XCY
        data = numpy.rollaxis(data, 2) # YXC
        dims = "YXC"

    if not dims == "YXC":
        raise NotImplementedError("Don't know how to handle dim order %s" % (dims,))

    if data.shape[-1] not in {3, 4}:
        logging.warning("RGB data has C dimension of length %d, instead of 3 or 4", data.shape[-1])

    if data.dtype != numpy.uint8:
        logging.warning("RGB data should be uint8, but is %s type", data.dtype)

    data = numpy.ascontiguousarray(data) # force memory placement
    md[model.MD_DIMS] = dims
    return model.DataArray(data, md)


def rescale_hq(data, shape):
    """
    Resize the image to the new given shape (smaller or bigger). It tries to
    smooth the pixels. Metadata is updated.
    data (DataArray or numpy.array): Data to be rescaled
    shape (tuple): the new shape of the image. It needs to be the same size as the data.shape.
    return (DataArray or numpy.array): The image rescaled. It has the same shape
        as the 'shape' parameter. The returned object has the same type of the 'data' parameter
    """
    # TODO: make it faster

    out = numpy.empty(shape, dtype=data.dtype)
    scale = tuple(n / o for o, n in zip(data.shape, shape))
    scipy.ndimage.interpolation.zoom(data, zoom=scale, output=out, order=1, prefilter=False)

    # Update the metadata
    if hasattr(data, "metadata"):
        out = model.DataArray(out, dict(data.metadata))
        # update each metadata which is linked to the pixel size
        # Metadata that needs to be divided by the scale (zoom => decrease)
        for k in {model.MD_PIXEL_SIZE, model.MD_BINNING}:
            try:
                ov = data.metadata[k]
            except KeyError:
                continue
            try:
                out.metadata[k] = tuple(o / s for o, s in zip(ov, scale))
            except Exception:
                logging.exception("Failed to update metadata '%s' when rescaling by %s",
                                  k, scale)
        # Metadata that needs to be multiplied by the scale (zoom => increase)
        for k in {model.MD_AR_POLE}:
            try:
                ov = data.metadata[k]
            except KeyError:
                continue
            try:
                out.metadata[k] = tuple(o * s for o, s in zip(ov, scale))
            except Exception:
                logging.exception("Failed to update metadata '%s' when rescaling by %s",
                                  k, scale)

    return out


def Subtract(a, b):
    """
    Subtract 2 images, with clipping if needed
    a (DataArray)
    b (DataArray or scalar)
    return (DataArray): a - b, with same dtype and metadata as a
    """
    # TODO: see if it is more useful to upgrade the type to a bigger if overflow
    if a.dtype.kind in "bu":
        # avoid underflow so that 1 - 2 = 0 (and not 65536)
        return numpy.maximum(a, b) - b
    else:
        # TODO handle under/over-flows with integer types (127 - (-1) => -128)
        return (a - b)

# TODO: use VIPS to be fast?
def Average(images, rect, mpp, merge=0.5):
    """
    mix the given images into a big image so that each pixel is the average of each
     pixel (separate operation for each colour channel).
    images (list of RGB DataArrays)
    merge (0<=float<=1): merge ratio of the first and second image (IOW: the
      first image is weighted by merge and second image by (1-merge))
    """
    # TODO: is ok to have a image = None?


    # TODO: (once the operator callable is clearly defined)
    raise NotImplementedError()

# TODO: add operator Screen


def mergeMetadata(current, correction=None):
    """
    Applies the correction metadata to the current metadata.

    This function is used in order to apply the correction metadata
    generated by the overlay stream to the optical images.

    In case there is some correction metadata (i.e. MD_*_COR) in the current
    dict this is updated with the corresponding metadata found in correction
    dict. However, if this particular metadata is not present in correction dict
    while it exists in current dict, it remains as is and its current value is
    used e.g. in fine alignment for Delphi, MD_ROTATION_COR of the SEM image is
    already present in the current metadata to compensate for MD_ROTATION, thus
    it is omitted in the correction metadata returned by the overlay stream.

    current (dict): original metadata, it will be updated, with the *_COR
      metadata removed if it was present.
    correction (dict or None): metadata with correction information, if None,
      will use current to find the correction metadata.
    """
    if correction is not None:
        current.update(correction)

    # TODO: rotation and position correction should use addition, not subtraction
    if model.MD_ROTATION_COR in current:
        # Default rotation is 0 rad if not specified
        rotation_cor = current[model.MD_ROTATION_COR]
        rotation = current.get(model.MD_ROTATION, 0)
        current[model.MD_ROTATION] = (rotation - rotation_cor) % (math.pi * 2)

    if model.MD_POS_COR in current:
        # Default position is (0, 0) if not specified
        position_cor = current[model.MD_POS_COR]
        position = current.get(model.MD_POS, (0, 0))

        current[model.MD_POS] = (position[0] - position_cor[0],
                                 position[1] - position_cor[1])

    if model.MD_SHEAR_COR in current:
        # Default shear is 0 if not specified
        shear_cor = current[model.MD_SHEAR_COR]
        shear = current.get(model.MD_SHEAR, 0)

        current[model.MD_SHEAR] = shear - shear_cor

    # There is no default pixel size (though in some case sensor pixel size can
    # be used as a fallback)
    if model.MD_PIXEL_SIZE in current:
        pxs = current[model.MD_PIXEL_SIZE]
        pxs_cor = current.get(model.MD_PIXEL_SIZE_COR, (1, 1))
        current[model.MD_PIXEL_SIZE] = (pxs[0] * pxs_cor[0], pxs[1] * pxs_cor[1])
    elif model.MD_PIXEL_SIZE_COR in current:
        logging.info("Cannot correct pixel size of data with unknown pixel size")

    # remove correction metadata (to make it clear the correction has been applied)
    for k in (model.MD_ROTATION_COR, model.MD_PIXEL_SIZE_COR, model.MD_POS_COR, model.MD_SHEAR_COR):
        if k in current:
            del current[k]

def mergeTiles(tiles):
    """"
    Merge tiles into one DataArray
    tiles (tuple of tuple of DataArray): Tiles to be merged
    return (DataArray): Merge of all the tiles
    """

    def get_corner_pos(tile, cm):
        md = tile.metadata
        dims = md.get(model.MD_DIMS, "CTZYX"[-tile.ndim::])
        tile_shape = [tile.shape[dims.index('X')], tile.shape[dims.index('Y')]]
        corner_dist_to_center_pixels = numpy.array([cm[0] * tile_shape[0]/2, cm[1] * tile_shape[1]/2])
        corner_dist_to_center_pixels = numpy.matrix(corner_dist_to_center_pixels).getT()
        tmat = get_img_transformation_matrix(tiles[0][0].metadata)
        rel_centerw = tmat * corner_dist_to_center_pixels
        rel_centerw = numpy.ravel(rel_centerw)
        centerw = tile.metadata[model.MD_POS]
        return [rel_centerw[0] + centerw[0], rel_centerw[1] + centerw[1]]


    height = 0
    for tile in tiles[0]:
        height += tile.shape[0]

    width = 0
    for tiles_column in tiles:
        width += tiles_column[0].shape[1]

    result_shape = (height, width)
    # TODO must work when the channel dimension is not the last
    if len(tiles[0][0].shape) == 3:
        result_shape = result_shape + (tiles[0][0].shape[2],)

    # TODO support multiple channels
    result = numpy.zeros(result_shape, dtype=tiles[0][0].dtype)
    result = model.DataArray(result, tiles[0][0].metadata.copy())

    width_sum = 0
    for tiles_column in tiles:
        tile_width = tiles_column[0].shape[1]
        height_sum = 0
        for tile in tiles_column:
            tile_height = tile.shape[0]
            result[height_sum:(height_sum + tile_height), width_sum:(width_sum + tile_width)] = \
                tile
            height_sum += tile_height

        width_sum += tile_width

    num_rows = len(tiles)
    num_cols = len(tiles[0])

    first_tile_pos = get_corner_pos(tiles[0][0], [-1, -1])

    last_tile = tiles[num_rows - 1][num_cols - 1]
    last_tile_pos = get_corner_pos(last_tile, [1, 1])

    pos = tuple((ftp + ltp) / 2 for ftp, ltp in zip(first_tile_pos, last_tile_pos))
    result.metadata[model.MD_POS] = pos

    return result

def _getBoundingBox(content):
    """
    Compute the physical bounding-box of the given DataArray(Shadow)
    content (DataArray(Shadow)): The data of the image
    return (tuple(ltbr)): left,top,bottom,right positions in world coordinates
    """
    md = content.metadata
    # get the pixel size of the full image
    # TODO check if an exception must be raised here
    ps = md.get(model.MD_PIXEL_SIZE, (1e-6, 1e-6))

    dims = md.get(model.MD_DIMS, "CTZYX"[-content.ndim::])
    img_shape = (content.shape[dims.index('X')], content.shape[dims.index('Y')])
    # half shape on world coordinates
    half_shape_wc = (
        img_shape[0] * ps[0] / 2,
        img_shape[1] * ps[1] / 2,
    )
    md_pos = md.get(model.MD_POS, (0.0, 0.0))
    rect = (
        md_pos[0] - half_shape_wc[0],
        md_pos[1] - half_shape_wc[1],
        md_pos[0] + half_shape_wc[0],
        md_pos[1] + half_shape_wc[1],
    )
    return rect
