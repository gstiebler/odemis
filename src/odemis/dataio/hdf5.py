# -*- coding: utf-8 -*-
'''
Created on 14 Jan 2013

@author: Éric Piel

Copyright © 2013 Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms 
of the GNU General Public License version 2 as published by the Free Software 
Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with 
Odemis. If not, see http://www.gnu.org/licenses/.
'''
from __future__ import division

import h5py
import logging
import numpy
from odemis import model
from odemis.util import spectrum
import os
import time


# User-friendly name
FORMAT = "HDF5"
# list of file-name extensions possible, the first one is the default when saving a file
EXTENSIONS = [u".h5", u".hdf5"]

# We are trying to follow the same format as SVI, as defined here:
# http://www.svi.nl/HDF5
# A file follows this structure:
# + /
#   + Preview (this our extension, to contain thumbnails)
#     + RGB image (*) (HDF5 Image with Dimension Scales)
#     + DimensionScale*
#     + *Offset (position on the axis)
#   + AcquisitionName (one per set of emitter/detector)
#     + ImageData
#       + Image (HDF5 Image with Dimension Scales CTZXY)
#       + DimensionScale*
#       + *Offset (position on the axis)
#     + PhysicalData
#     + SVIData (Not necessary for us)


# Image is an official extension to HDF5:
# http://www.hdfgroup.org/HDF5/doc/ADGuide/ImageSpec.html

# TODO: Document all our extensions (Preview, AR images, Rotation...)
# Angular Resolved images (acquired by the SPARC) are recorded such as:
# * Each CCD image is a separate acquisition, containing the raw data
# * For each acquisition, the offset contains the position of the ebeam
# * For each acquisition, a PhysicalData/PolePosition contains the X,Y
#   coordinates (in px) of the mirror pole on the raw data.

# Rotation information is saved in ImageData/Rotation as a series of floats
# (of 3 or more dimensions, corresponding to X, Y, Z dimensions). It represents
# the rotation vector (with right-hand rule). See the wikipedia article for
# details. It's basically a vector which represents the plan of rotation by its
# direction, and the angle (in rad) by its norm. The rotation is always applied
# on the center of the data. For example, to rotate a 2D image by 0.7 rad
# counter clockwise, the rotation vector would be 0, 0, 0.7

# Data is normally always recoded as 5 dimensions in order CTZYX. One exception
# is for the RGB (looking) data, in which case it's recorded only in 3
# dimensions, CYX (that allows to easily open it in hdfview).

# h5py doesn't implement explicitly HDF5 image, and is not willing to cf:
# http://code.google.com/p/h5py/issues/detail?id=157
def _create_image_dataset(group, dataset_name, image, **kwargs):
    """
    Create a dataset respecting the HDF5 image specification
    http://www.hdfgroup.org/HDF5/doc/ADGuide/ImageSpec.html
   
    group (HDF group): the group that will contain the dataset
    dataset_name (string): name of the dataset
    image (numpy.ndimage): the image to create. It should have at least 2 dimensions
    returns the new dataset
    """
    assert(len(image.shape) >= 2)
    image_dataset = group.create_dataset(dataset_name, data=image, **kwargs)

    # numpy.string_ is to force fixed-length string (necessary for compatibility)
    image_dataset.attrs["CLASS"] = numpy.string_("IMAGE")
    # Colour image?
    if image.ndim == 3 and (image.shape[-3] == 3 or image.shape[-1] == 3):
        # TODO: check dtype is int?
        image_dataset.attrs["IMAGE_SUBCLASS"] = numpy.string_("IMAGE_TRUECOLOR")
        image_dataset.attrs["IMAGE_COLORMODEL"] = numpy.string_("RGB")
        if image.shape[-3] == 3:
            # Stored as [pixel components][height][width]
            image_dataset.attrs["INTERLACE_MODE"] = numpy.string_("INTERLACE_PLANE")
        else: # This is the numpy standard
            # Stored as [height][width][pixel components]
            image_dataset.attrs["INTERLACE_MODE"] = numpy.string_("INTERLACE_PIXEL")
    else:
        image_dataset.attrs["IMAGE_SUBCLASS"] = numpy.string_("IMAGE_GRAYSCALE")
        image_dataset.attrs["IMAGE_WHITE_IS_ZERO"] = numpy.array(0, dtype="uint8")
        image_dataset.attrs["IMAGE_MINMAXRANGE"] = [image.min(), image.max()]

    image_dataset.attrs["DISPLAY_ORIGIN"] = numpy.string_("UL") # not rotated
    image_dataset.attrs["IMAGE_VERSION"] = numpy.string_("1.2")

    return image_dataset

def _read_image_dataset(dataset):
    """
    Get a numpy array from a dataset respecting the HDF5 image specification.
    returns (numpy.ndimage): it has at least 2 dimensions and if RGB, it has
     a 3 dimensions and the metadata MD_DIMS indicates the order.
    raises
     IOError: if it doesn't conform to the standard
     NotImplementedError: if the image uses so fancy standard features
    """
    # check basic format
    if len(dataset.shape) < 2:
        raise IOError("Image has a shape of %s" % (dataset.shape,))

    if dataset.attrs.get("IMAGE_VERSION") != "1.2":
        logging.info("Trying to read an HDF5 image of unsupported version")

    # conversion is almost entirely different depending on subclass
    subclass = dataset.attrs.get("IMAGE_SUBCLASS", "IMAGE_GRAYSCALE")

    image = model.DataArray(dataset[...])
    if subclass == "IMAGE_GRAYSCALE":
        pass
    elif subclass == "IMAGE_TRUECOLOR":
        if len(dataset.shape) != 3:
            raise IOError("Truecolor image has a shape of %s" % (dataset.shape,))

        try:
            il_mode = dataset.attrs.get("INTERLACE_MODE")
        except KeyError:
            # TODO: guess il_mode from the shape
            raise IOError("Interlace mode missing")

        cm = dataset.attrs.get("IMAGE_COLORMODEL", "RGB") # optional attr
        if cm != "RGB":
            raise NotImplementedError("Unable to handle images of colormodel '%s'" % cm)

        if il_mode == "INTERLACE_PLANE":
            # colour is first dim
            image.metadata[model.MD_DIMS] = "CYX"
        elif il_mode == "INTERLACE_PIXEL":
            image.metadata[model.MD_DIMS] = "YXC"
        else:
            raise NotImplementedError("Unable to handle images of subclass '%s'" % subclass)

    else:
        raise NotImplementedError("Unable to handle images of subclass '%s'" % subclass)

    
    # TODO: support DISPLAY_ORIGIN
    dorig = dataset.attrs.get("DISPLAY_ORIGIN", "UL") 
    if dorig != "UL":
        logging.warning("Image rotation %d not handled", dorig)
    
    return image

def _add_image_info(group, dataset, image):
    """
    Adds the basic metadata information about an image (scale, offset, and rotation)
    group (HDF Group): the group that contains the dataset
    dataset (HDF Dataset): the image dataset
    image (DataArray >= 2D): image with metadata, the last 2 dimensions are Y and X (H,W)
    """
    # Note: DimensionScale support is only part of h5py since v2.1
    
    # Dimensions
    l = image.ndim
    dims = image.metadata.get(model.MD_DIMS, "CTZYX"[-l::])
            
    for i, d in enumerate(dataset.dims):
        d.label = dims[i]
    
    # FIXME: We map the position of the center to X/YOffset. That's quite
    # contrary to the feeling that the position of a pixel should be read as
    # XOffset + i * DimensionScaleX. => It would be more logical to set
    # X/YOffset as the position of pixel 0,0. (The drawback being that we need
    # to have a precise idea of the size of a pixel to position the image)

    # Offset
    if model.MD_POS in image.metadata:
        pos = image.metadata[model.MD_POS]
        group["XOffset"] = pos[0]
        _h5svi_set_state(group["XOffset"], ST_REPORTED)
        group["XOffset"].attrs["UNIT"] = "m" # our extension
        group["YOffset"] = pos[1]
        _h5svi_set_state(group["YOffset"], ST_REPORTED)
        group["YOffset"].attrs["UNIT"] = "m" # our extension

    # Time
    # TODO:
    # Surprisingly (for such a usual type), time storage is a mess in HDF5.
    # The documentation states that you can use H5T_TIME, but it is
    # "is not supported. If H5T_TIME is used, the resulting data will be readable
    # and modifiable only on the originating computing platform; it will not be
    # portable to other platforms.". It appears many format are allowed.
    # In addition in h5py, it's indicated as "deprecated" (although it seems
    # it was added in the latest version of HDF5).
    # Moreover, the only types available are 32 and 64 bits integers as number
    # of seconds since epoch. No past, no milliseconds, no time-zone.
    # So there are other proposals like in in F5
    # (http://sciviz.cct.lsu.edu/papers/2007/F5TimeSemantics.pdf) to represent
    # time with a float, a unit and an offset.
    # KNMI uses a string like this: DD-MON-YYYY;HH:MM:SS.sss.
    # (cf http://www.knmi.nl/~beekhuis/documents/publicdocs/ir2009-01_hdftag36.pdf)
    # So, to not solve anything, we save the date as a float representing the
    # Unix time. At least it makes Huygens happy.
    if model.MD_ACQ_DATE in image.metadata:
        # For a ISO 8601 string:
#        ad = datetime.utcfromtimestamp(image.metadata[model.MD_ACQ_DATE])
#        adstr = ad.strftime("%Y-%m-%dT%H:%M:%S.%f")
#        group["TOffset"] = adstr
        group["TOffset"] = image.metadata[model.MD_ACQ_DATE]
        _h5svi_set_state(group["TOffset"], ST_REPORTED)
    else:
        group["TOffset"] = time.time()
        _h5svi_set_state(group["TOffset"], ST_DEFAULT)
    group["TOffset"].attrs["UNIT"] = "s" # our extension

    # Scale
    if model.MD_PIXEL_SIZE in image.metadata:
        # DimensionScales are not clearly explained in the specification to
        # understand what they are supposed to represent. Surprisingly, there
        # is no official way to attach a unit.
        # Huygens seems to consider it's in m
        xpos = dims.index("X")
        ypos = dims.index("Y")
        pxs = image.metadata[model.MD_PIXEL_SIZE]
        group["DimensionScaleX"] = pxs[0]
        group["DimensionScaleX"].attrs["UNIT"] = "m" # our extension
        _h5svi_set_state(group["DimensionScaleX"], ST_REPORTED)
        group["DimensionScaleY"] = pxs[1]
        group["DimensionScaleY"].attrs["UNIT"] = "m"
        _h5svi_set_state(group["DimensionScaleY"], ST_REPORTED)
        # No clear what's the relation between this name and the label
        dataset.dims.create_scale(group["DimensionScaleX"], "X")
        dataset.dims.create_scale(group["DimensionScaleY"], "Y")
        dataset.dims[xpos].attach_scale(group["DimensionScaleX"])
        dataset.dims[ypos].attach_scale(group["DimensionScaleY"])

    # Unknown data, but SVI needs them to take the scales into consideration
    if "Z" in dims:
        zpos = dims.index("Z")
        group["ZOffset"] = 0.0
        _h5svi_set_state(group["ZOffset"], ST_DEFAULT)
        group["DimensionScaleZ"] = 1e-3 # m
        group["DimensionScaleZ"].attrs["UNIT"] = "m"
        dataset.dims.create_scale(group["DimensionScaleZ"], "Z")
        _h5svi_set_state(group["DimensionScaleZ"], ST_DEFAULT)
        dataset.dims[zpos].attach_scale(group["DimensionScaleZ"])

        # Put here to please Huygens
        # Seems to be the coverslip position, ie, the lower and upper glass of
        # the sample. Not clear what's the relation with ZOffset.
        group["PrimaryGlassMediumInterfacePosition"] = 0.0 # m?
        _h5svi_set_state(group["PrimaryGlassMediumInterfacePosition"], ST_DEFAULT)
        group["SecondaryGlassMediumInterfacePosition"] = 1.0 # m?
        _h5svi_set_state(group["SecondaryGlassMediumInterfacePosition"], ST_DEFAULT)

    if "T" in dims:
        tpos = dims.index("T")
        group["DimensionScaleT"] = 1.0 # s
        group["DimensionScaleT"].attrs["UNIT"] = "s"
        # No clear what's the relation between this name and the label
        dataset.dims.create_scale(group["DimensionScaleT"], "T")
        _h5svi_set_state(group["DimensionScaleT"], ST_DEFAULT)
        dataset.dims[tpos].attach_scale(group["DimensionScaleT"])

    # Wavelength (for spectrograms)
    if ("C" in dims and
        set(image.metadata.keys()) & {model.MD_WL_LIST, model.MD_WL_POLYNOMIAL}):
        try:
            # polynomial of degree = 2 => linear, so use compact notation
            if (model.MD_WL_POLYNOMIAL in image.metadata and
                len(image.metadata[model.MD_WL_POLYNOMIAL]) == 2):
                pn = image.metadata[model.MD_WL_POLYNOMIAL]
                group["COffset"] = pn[0]
                _h5svi_set_state(group["COffset"], ST_REPORTED)
                group["DimensionScaleC"] = pn[1] # m
            else:
                wll = spectrum.get_wavelength_per_pixel(image)
                # list or polynomial of degree > 2 => store the values of each
                # pixel index explicitly. We follow another way to express
                # scaling in HDF5.
                group["DimensionScaleC"] = wll # m

            group["DimensionScaleC"].attrs["UNIT"] = "m"
            dataset.dims.create_scale(group["DimensionScaleC"], "C")
            _h5svi_set_state(group["DimensionScaleC"], ST_REPORTED)
            cpos = dims.index("C")
            dataset.dims[cpos].attach_scale(group["DimensionScaleC"])
        except Exception:
            logging.warning("Failed to record wavelength information, "
                            "it will not be saved.")
        

    # Rotation (3-scalar): X,Y,Z of the rotation vector, with the norm being the
    # angle in radians (according to the right-hand rule)
    if model.MD_ROTATION in image.metadata:
        # In Odemis we only support 2D rotation, so just around Z
        group["Rotation"] = (0, 0, image.metadata[model.MD_ROTATION])
        _h5svi_set_state(group["Rotation"], ST_REPORTED)
        group["Rotation"].attrs["UNIT"] = "rad"

def _read_image_info(group):
    """
    Read the basic metadata information about an image (scale and offset)
    group (HDF Group): the group "ImageData" that contains the image (named "Image")
    return (dict (MD_* -> Value)): the metadata that could be read
    """
    dataset = group["Image"]
    md = {}
    # Offset
    try:
        pos = (float(group["XOffset"][()]), float(group["YOffset"][()]))
        md[model.MD_POS] = pos
    except Exception:
        pass
    try:
        acq_date = float(group["TOffset"][()])
        md[model.MD_ACQ_DATE] = acq_date
        # TODO: add scale for each Z ??
    except Exception:
        pass

    # Scale
    try:
        pxs = [None, None]
        for dim in dataset.dims:
            if dim.label == "X":
                pxs[0] = float(dim[0][()])
            if dim.label == "Y":
                pxs[1] = float(dim[0][()])

        md[model.MD_PIXEL_SIZE] = tuple(pxs)
    except Exception:
        pass

    # Wavelength is only if the data has a C dimension and it has one number 
    # for the scale (linear polynomial) or it it has a list of wavelengths (one 
    # per pixel).
    # Note that not all data has information, for example RGB images, or
    # fluorescence images have no scale (but the SVI flavour has several
    # metadata related in the PhysicalData group).
    try:
        for i, dim in enumerate(dataset.dims):
            if dim.label == "C":
                if dim[0].shape == (dataset.shape[i],):
                    md[model.MD_WL_LIST] = map(float, dim[0][...].tolist())
                elif dim[0].shape == ():
                    pn = [float(group["COffset"][()]),
                          float(dim[0][()])]
                    md[model.MD_WL_POLYNOMIAL] = pn
    except Exception:
        pass

    try:
        rot = group["Rotation"]
        md[model.MD_ROTATION] = float(rot[2])
        if rot[0] != 0 or rot[1] != 0:
            logging.info("Metadata contains rotation vector %s, which cannot be"
                         " fully reproduced in Odemis.", rot) 

    except Exception:
        pass

    return md


def _parse_physical_data(pdgroup, da):
    """
    Parse the metadata found in PhysicalData, and cut the DataArray if necessary.
    pdgroup (HDF Group): the group "PhysicalData" associated to an image
    da (DataArray): the DataArray that was obtained by reading the ImageData
    returns (list of DataArrays): The same data, but broken into smaller 
      DataArrays if necessary, and with additional metadata.
    """
    # The information in PhysicalData might be different for each channel (e.g.
    # fluorescence image). In this case, the DA must be separated into smaller
    # ones, per channel.
    # For now, we detect this by only checking the shape of the metadata (>1),
    # and just ChannelDescription

    try:
        cd = pdgroup["ChannelDescription"]
        n = numpy.prod(cd.shape) # typically like (N,)
    except KeyError:
        n = 0 # that means all are together

    if n > 1:
        # need to separate it
        if n != da.shape[0]:
            logging.warning("Image has %d channels and %d metadata, failed to map",
                            da.shape[0], n)
            das = [da]
        else:
            # list(da) does almost what we need, but metadata is shared
            das = [model.DataArray(c, da.metadata.copy()) for c in da]
    else:
        das = [da]

    for i, d in enumerate(das):
        md = d.metadata
        try:
            cd = pdgroup["ChannelDescription"][i]
            md[model.MD_DESCRIPTION] = unicode(cd)
        except (KeyError, IndexError):
            # maybe Title is more informative... but it's not per channel
            try:
                title = pdgroup["Title"][()]
                md[model.MD_DESCRIPTION] = unicode(title)
            except (KeyError, IndexError):
                pass

        # MicroscopeMode helps us to find out the bandwidth of the wavelength
        # and it's also a way to keep it stable, if saving the data again.
        h_width = 1e-9 # 1 nm : default is to just almost keep the value
        try:
            mm = pdgroup["MicroscopeMode"][i]
            if mm == MM_FLUORESCENCE:
                h_width = 10e-9 # 10 nm => narrow band
            if mm == MM_TRANSMISSION: # we set it for brightfield
                h_width = 100e-9 # 100 nm => large band
        except (KeyError, IndexError, ValueError):
            pass

        try:
            ds = pdgroup["ExcitationWavelength"]
            xwl = float(ds[i]) # in m
            state = _h5svi_get_state(ds)
            if state and state[i] == ST_INVALID:
                raise ValueError
            md[model.MD_IN_WL] = (xwl - h_width, xwl + h_width)
        except (KeyError, IndexError, ValueError):
            pass

        try:
            ds = pdgroup["EmissionWavelength"]
            ewl = float(ds[i]) # in m
            state = _h5svi_get_state(ds)
            if state and state[i] == ST_INVALID:
                raise ValueError
            md[model.MD_OUT_WL] = (ewl - h_width, ewl + h_width)
        except (KeyError, IndexError, ValueError):
            pass

        try:
            ds = pdgroup["Magnification"]
            mag = float(ds[i])
            state = _h5svi_get_state(ds)
            if state and state[i] == ST_INVALID:
                raise ValueError
            md[model.MD_LENS_MAG] = mag
        except (KeyError, IndexError, ValueError):
            pass

        # Our extended metadata
        try:
            ds = pdgroup["IntegrationTime"]
            it = float(ds[i]) # s
            state = _h5svi_get_state(ds)
            if state and state[i] == ST_INVALID:
                raise ValueError
            md[model.MD_EXP_TIME] = it
        except (KeyError, IndexError, ValueError):
            pass

        try:
            ds = pdgroup["PolePosition"]
            pp = tuple(ds[i]) # px
            state = _h5svi_get_state(ds)
            if state and state[i] == ST_INVALID:
                raise ValueError
            md[model.MD_AR_POLE] = pp
        except (KeyError, IndexError, ValueError):
            pass

    return das

# Enums used in SVI HDF5
# State: how "trustable" is the value
ST_INVALID = 111
ST_DEFAULT = 112
ST_ESTIMATED = 113
ST_REPORTED = 114
ST_VERIFIED = 115
_dtstate = h5py.special_dtype(enum=('i', {
     "Invalid":ST_INVALID, "Default":ST_DEFAULT, "Estimated":ST_ESTIMATED,
     "Reported":ST_REPORTED, "Verified":ST_VERIFIED}))

# MicroscopeMode
MM_NONE = 0
MM_TRANSMISSION = 1
MM_REFLECTION = 2
MM_FLUORESCENCE = 3
_dtmm = h5py.special_dtype(enum=('i', {
     "None":MM_NONE, "Transmission":MM_TRANSMISSION ,
     "Reflection":MM_REFLECTION, "Fluorescence":MM_FLUORESCENCE}))
_dictmm = h5py.check_dtype(enum=_dtmm)
# MicroscopeType
MT_NONE = 111
MT_WIDEFIELD = 112
MT_CONFOCAL = 113
MT_4PIEXCITATION = 114
MT_NIPKOWDISKCONFOCAL = 115
MT_GENERICSENSOR = 118
_dtmt = h5py.special_dtype(enum=('i', {
    "None":MT_NONE, "WideField":MT_WIDEFIELD, "Confocal":MT_CONFOCAL,
    "4PiExcitation":MT_4PIEXCITATION, "NipkowDiskConfocal":MT_NIPKOWDISKCONFOCAL,
    "GenericSensor":MT_GENERICSENSOR}))
_dictmt = h5py.check_dtype(enum=_dtmt)
# ImagingDirection
ID_UPWARD = 0
ID_DOWNWARD = 1
ID_BOTH = 2
_dtid = h5py.special_dtype(enum=('i', {
    "Upward":ID_UPWARD, "Downward":ID_DOWNWARD, "Both":ID_BOTH}))
_dictid = h5py.check_dtype(enum=_dtid)

def _h5svi_set_state(dataset, state):
    """
    Set the "State" of a dataset: the confidence that can be put in the value
    dataset (Dataset): the dataset
    state (int or list of int): the state value (ST_*) which will be duplicated
     as many times as the shape of the dataset. If it's a list, it will be directly
     used, as is.
    """

    # the state should be the same shape as the dataset
    if isinstance(state, int):
        fullstate = numpy.empty(shape=dataset.shape, dtype=_dtstate)
        fullstate.fill(state)
    else:
        fullstate = numpy.array(state, dtype=_dtstate)

    dataset.attrs["State"] = fullstate

def _h5svi_get_state(dataset, default=None):
    """
    Read the "State" of a dataset: the confidence that can be put in the value
    dataset (Dataset): the dataset
    default: to be returned if no state is present
    return state (int or list of int): the state value (ST_*) which will be duplicated
     as many times as the shape of the dataset. If it's a list, it will be directly
     used, as is. If not state available, default is returned.
    """
    try:
        state = dataset.attrs["State"]
    except IndexError:
        return default

    return state.tolist()

def _h5py_enum_commit(group, name, dtype):
    """
    Commit (=save under a name) a enum to a group
    group (h5py.Group)
    name (string)
    dtype (dtype)
    """
    enum_type = h5py.h5t.py_create(dtype, logical=True)
    enum_type.commit(group.id, name)
    #TODO: return the TypeEnumID created?

def _add_image_metadata(group, image, mds):
    """
    Adds the basic metadata information about an image (scale and offset)
    group (HDF Group): the group that will contain the metadata (named "PhysicalData")
    image (DataArray): image (with global metadata)
    mds (None or list of dict): metadata for each channel
    """
    gp = group.create_group("PhysicalData")

    dtvlen_str = h5py.special_dtype(vlen=str)
    # TODO indicate correctly the State of the information (especially if it's unknown)

    if mds is None:
        mds = [image.metadata]

    # All values are duplicated by channel, excepted for Title
    gdesc = [md.get(model.MD_DESCRIPTION, "") for md in mds]
    gp["Title"] = ", ".join(gdesc)

    cdesc = [md.get(model.MD_DESCRIPTION, "") for md in mds]
    gp["ChannelDescription"] = numpy.array(cdesc, dtype=dtvlen_str)
    _h5svi_set_state(gp["ChannelDescription"], ST_ESTIMATED)

    # Wavelengths are not a band, but a single value, so we pick the center
    xwls = [md.get(model.MD_IN_WL) for md in mds]
    gp["ExcitationWavelength"] = [1e-9 if v is None else numpy.mean(v) for v in xwls] # in m
    state = [ST_INVALID if v is None else ST_REPORTED for v in xwls]
    _h5svi_set_state(gp["ExcitationWavelength"], state)

    ewls = [md.get(model.MD_OUT_WL) for md in mds]
    gp["EmissionWavelength"] = [1e-9 if v is None else numpy.mean(v) for v in ewls] # in m
    state = [ST_INVALID if v is None else ST_REPORTED for v in ewls]
    _h5svi_set_state(gp["EmissionWavelength"], state)

    mags = [md.get(model.MD_LENS_MAG) for md in mds]
    gp["Magnification"] = [1.0 if m is None else m for m in mags]
    state = [ST_INVALID if v is None else ST_REPORTED for v in mags]
    _h5svi_set_state(gp["Magnification"], state)

    # MicroscopeMode
    _h5py_enum_commit(gp, "MicroscopeModeEnumeration", _dtmm)
    # MicroscopeType
    _h5py_enum_commit(gp, "MicroscopeTypeEnumeration", _dtmt)
    # ImagingDirection
    _h5py_enum_commit(gp, "ImagingDirectionEnumeration", _dtid)
    mm, mt, id = [], [], []
    # MicroscopeMode: if IN_WL => fluorescence/brightfield, otherwise SEM (=Reflection?)
    for md in mds:
        # FIXME: this is true only for the SECOM
        if model.MD_IN_WL in md:
            iwl = md[model.MD_IN_WL]
            if abs(iwl[1] - iwl[0]) < 100e-9:
                mm.append("Fluorescence")
                mt.append("WideField")
                id.append("Downward")
            else:
                mm.append("Transmission")  # Brightfield
                mt.append("WideField")
                id.append("Downward")
        else:
            mm.append("Reflection")  # SEM
            mt.append("GenericSensor") # ScanningElectron?
            id.append("Upward")
    # Microscope* is the old format, Microscope*Str is new format
    # FIXME: it seems h5py doesn't allow to directly set the dataset type to a
    # named type (it always creates a new transient type), unless you redo
    # all make_new_dset() by hand.
    gp["MicroscopeMode"] = numpy.array([_dictmm[m] for m in mm], dtype=_dtmm)
    _h5svi_set_state(gp["MicroscopeMode"], ST_REPORTED)
    # For the *Str, Huygens expects a space separated string (scalar), _but_
    # still wants an array for the state of each channel.
    gp["MicroscopeModeStr"] = " ".join([m.lower() for m in mm])
    _h5svi_set_state(gp["MicroscopeModeStr"], numpy.array([ST_REPORTED] * len(mds), dtype=_dtstate))
    gp["MicroscopeType"] = numpy.array([_dictmt[t] for t in mt], dtype=_dtmt)
    _h5svi_set_state(gp["MicroscopeType"], ST_REPORTED)
    gp["MicroscopeTypeStr"] = " ".join([t.lower() for t in mt])
    _h5svi_set_state(gp["MicroscopeTypeStr"], numpy.array([ST_REPORTED] * len(mds), dtype=_dtstate))
    gp["ImagingDirection"] = numpy.array([_dictid[d] for d in id], dtype=_dtid)
    _h5svi_set_state(gp["ImagingDirection"], ST_REPORTED)
    gp["ImagingDirectionStr"] = " ".join([d.lower() for d in id])
    _h5svi_set_state(gp["ImagingDirectionStr"], numpy.array([ST_REPORTED] * len(mds), dtype=_dtstate))

    # Below are almost entirely made-up values, present just to please Huygens
    # TODO: should allow the user to specify it in the preferences: 1=>vacuum, 1.5 => glass/oil
    gp["RefractiveIndexLensImmersionMedium"] = [1.515] * len(mds) # ratio (no unit)
    _h5svi_set_state(gp["RefractiveIndexLensImmersionMedium"], ST_DEFAULT)
    gp["RefractiveIndexSpecimenEmbeddingMedium"] = [1.515] * len(mds) # ratio (no unit)
    _h5svi_set_state(gp["RefractiveIndexSpecimenEmbeddingMedium"], ST_DEFAULT)

    # Only for confocal microscopes
    gp["BackprojectedIlluminationPinholeSpacing"] = [2.53e-6] * len(mds) # unit? m?
    _h5svi_set_state(gp["BackprojectedIlluminationPinholeSpacing"], ST_DEFAULT)
    gp["BackprojectedIlluminationPinholeRadius"] = [280e-9] * len(mds) # unit? m?
    _h5svi_set_state(gp["BackprojectedIlluminationPinholeRadius"], ST_DEFAULT)
    gp["BackprojectedPinholeRadius"] = [280e-9] * len(mds) # unit? m?
    _h5svi_set_state(gp["BackprojectedPinholeRadius"], ST_DEFAULT)

    # TODO: should come from the microscope model?
    gp["NumericalAperture"] = [1.4] * len(mds) # ratio (no unit)
    _h5svi_set_state(gp["NumericalAperture"], ST_DEFAULT)
    gp["ObjectiveQuality"] = [80] * len(mds) # unit? int [0->100] = percentage of respect to the theory?
    _h5svi_set_state(gp["ObjectiveQuality"], ST_DEFAULT)

    # Only for confocal microscopes?
    gp["ExcitationBeamOverfillFactor"] = [2.0] * len(mds) # unit?
    _h5svi_set_state(gp["ExcitationBeamOverfillFactor"], ST_DEFAULT)

    # Only for fluorescence acquisitions. Almost always 1, excepted for super fancy techniques.
    # Number of simultaneously absorbed photons by a fluorophore in a fluorescence event
    gp["ExcitationPhotonCount"] = [1] * len(mds) # photons
    _h5svi_set_state(gp["ExcitationPhotonCount"], ST_DEFAULT)


    # Below are additional metadata from us (Delmic)
    # IntegrationTime: time spent by each pixel to receive energy (in s)
    its, st_its = [], []
    for md in mds:
        if model.MD_DWELL_TIME in md:
            its.append(md[model.MD_DWELL_TIME])
            st_its.append(ST_REPORTED)
        elif model.MD_EXP_TIME in md:
            its.append(md[model.MD_EXP_TIME])
            st_its.append(ST_REPORTED)
        else:
            its.append(0)
            st_its.append(ST_INVALID)
    if not all(st == ST_INVALID for st in st_its):
        gp["IntegrationTime"] = its
        _h5svi_set_state(gp["IntegrationTime"], st_its)

    # PolePosition: position (in floating px) of the pole in the image
    # (only meaningful for AR/SPARC)
    pp, st_pp = [], []
    for md in mds:
        if model.MD_AR_POLE in md:
            pp.append(md[model.MD_AR_POLE])
            st_pp.append(ST_REPORTED)
        else:
            pp.append((0, 0))
            st_pp.append(ST_INVALID)
    if not all(st == ST_INVALID for st in st_pp):
        gp["PolePosition"] = pp
        _h5svi_set_state(gp["PolePosition"], st_pp)

    # TODO: model.MD_EBEAM_VOLTAGE, model.MD_EBEAM_SPOT_DIAM

def _add_svi_info(group):
    """
    Adds the information to indicate this file follows the SVI format
    group (HDF Group): the group that will contain the information
    """
    gi = group.create_group("SVIData")
    gi["Company"] = "Delmic"
    gi["FileSpecificationCompatibility"] = "0.01p0"
    gi["FileSpecificationVersion"] = "0.01d8"
    gi["ImageHistory"] = ""
    gi["URL"] = "www.delmic.com"

def _add_acquistion_svi(group, data, mds, **kwargs):
    """
    Adds the acquisition data according to the sub-format by SVI
    group (HDF Group): the group that will contain the metadata (named "PhysicalData")
    data (DataArray): image with (global) metadata, all the images must
      have the same shape.
    mds (None or list of dict): metadata for each C of the image (if different) 
    """
    gi = group.create_group("ImageData")

    # StateEnumeration
    # FIXME: should be done by _h5svi_set_state (and used)
    _h5py_enum_commit(group, "StateEnumeration", _dtstate)

    # TODO: use scaleoffset to store the number of bits used (MD_BPP)
    ids = _create_image_dataset(gi, "Image", data, **kwargs)
    # FIXME: if ids.CLASS=IMAGE on 64 bits => attach_scale doesn't work
    # as a workaround, we temporarily change it
    # Reported to h5py on 03-02-2014 -> it's a bug in HDF5 lib, but works on 32 bits.
    ids.attrs["CLASS"] = numpy.string_("BOOO")
    _add_image_info(gi, ids, data)
    ids.attrs["CLASS"] = numpy.string_("IMAGE")
    _add_image_metadata(group, data, mds)
    _add_svi_info(group)

def _findImageGroups(das):
    """
    Find groups of images which should be considered part of the same acquisition
    (be a channel of an Image in HDF5 SVI).
    das (list of DataArray): all the images, with dimensions ordered C(TZ)YX
    returns (list of list of DataArray): a list of "groups", each group is a list
     of DataArrays
    Note: it's a slightly different function from tiff._findImageGroups()
    """
    # We consider images to be part of the same group if they have:
    # * same shape
    # * metadata that show they were acquired by the same instrument
    # * same position
    # * same density (MPP)
    # * same rotation
    groups = []

    for i, da in enumerate(das):
        # try to find a matching group (compare just to the first picture)
        for g in groups:
            # If C != 1 => not possible to merge
            if da.shape[0] != 1: # C is always first dimension
                continue
            da0 = das[g[0]]
            if da0.shape != da.shape:
                continue
            if (da0.metadata.get(model.MD_HW_NAME) != da.metadata.get(model.MD_HW_NAME)
                or da0.metadata.get(model.MD_HW_VERSION) != da.metadata.get(model.MD_HW_VERSION)):
                continue
            if (da0.metadata.get(model.MD_PIXEL_SIZE) != da.metadata.get(model.MD_PIXEL_SIZE)
                or da0.metadata.get(model.MD_POS) != da.metadata.get(model.MD_POS)
                or da0.metadata.get(model.MD_ROTATION, 0) != da.metadata.get(model.MD_ROTATION, 0)
                ):
                continue
            # Found!
            g.append(i)
            break
        else:
            # Not found => create a new group
            groups.append([i])

    gdata = [[das[i] for i in g] for g in groups]
    return gdata

def _adjustDimensions(da):
    """
    Ensure the DataArray has 5 dimensions ordered CTZXY (as dictated by the HDF5 
    SVI convention). If it seems to contain RGB data, an exception is made to
    return just CYX data.
    da (DataArray)
    returns (DataArray): a new DataArray (possibly just a view) 
    """
    # Dimension names (default to CTZYX)
    l = da.ndim
    dims = da.metadata.get(model.MD_DIMS, "CTZYX"[-l::])
    md = dict(da.metadata)

    # Special cases for RGB
    if dims == "YXC":
        # convert to CYX
        da = numpy.rollaxis(da, 2)
        dims = "CYX"

    if dims == "CYX" and da.shape[0] in {3, 4}:
        md.update({model.MD_DIMS: dims})
        da = model.DataArray(da, md)
        return da

    dim_goal = "CTZYX"
    # Extend the missing dimensions to 1
    if l < 5:
        shape5d = (1,) * (5 - l) + da.shape
        da = da.reshape(shape5d)

    # fill up the dimensions by adding the missing ones
    while len(dims) < 5:
        for d in reversed(dim_goal):
            if d not in dims:
                dims = d + dims
                break

    # reorder dimensions so that they are in the expected order
    if dims != dim_goal:
        # roll the axes until they fit
        for i, d in enumerate(dim_goal):
            p = dims.index(d)
            da = numpy.rollaxis(da, p, i)
            dims[:i] + d + dims[i:p] + dims[p + 1:] # roll dims

    md.update({model.MD_DIMS: dims})
    da = model.DataArray(da, md)
    return da

def _groupImages(das):
    """
    Group images into larger ndarray, to follow the HDF5 SVI flavour.
    In practice, this only consists in merging data for multiple channels into
    one, and ordering/extending the shape to CTZYX.
    das (list of DataArray): all the images
    returns :
      acq (list of DataArrays): each group of data, with the (general) metadata 
      metadatas (list of (list of dict, or None)): for each item of acq, either
       None if the metadata is fully in acq or one metadata per channel.
    """
    # For each image: adjust dimensions
    adas = [_adjustDimensions(da) for da in das]
    
    # For each image, if C = 1, try to merge it to an existing group
    groups = _findImageGroups(adas)
    
    acq, mds = [], []
    
    # For each group:
    # * if alone, do nothing
    # * if many, merge along C
    for g in groups:
        if len(g) == 1:
            acq.append(g[0])
            mds.append(None)
        else:
            # merge along C (always axis 0)
            gdata = numpy.concatenate(g, axis=0)
            md = [d.metadata for d in g]
            # merge metadata
            # TODO: might need to be more clever for some metadata (eg, ACQ_DATE)
            gmd = {}
            map(gmd.update, md)
            gdata = model.DataArray(gdata, gmd)

            acq.append(gdata)
            mds.append(md)

    return acq, mds

def _updateRGBMD(da):
    """
    update MD_DIMS of the DataArray containing RGB if needed. Trying to guess
     according to the shape if necessary.
    da (DataArray): DataArray to update
    """
    if da.ndim != 3 or model.MD_DIMS in da.metadata:
        return

    # C dim is the one with 3 (or 4) elements
    if da.shape[0] in {3, 4}:
        dims = "CYX"
    elif da.shape[2] in {3, 4}:
        dims = "YXC"

    da.metadata[model.MD_DIMS] = dims

def _thumbFromHDF5(filename):
    """
    Read thumbnails from an HDF5 file.
    Expects to find them as IMAGE in Preview/Image.
    return (list of model.DataArray)
    """
    f = h5py.File(filename, "r")

    thumbs = []
    # look for the Preview directory
    try:
        grp = f["Preview"]
    except KeyError:
        # no thumbnail
        return thumbs

    # scan for images
    for name, ds in grp.items():
        # an image? (== has the attribute CLASS: IMAGE)
        if isinstance(ds, h5py.Dataset) and ds.attrs.get("CLASS") == "IMAGE":
            try:
                da = _read_image_dataset(ds)
            except Exception:
                logging.info("Skipping image '%s' which couldn't be read.", name)
                continue

            if name == "Image":
                try:
                    da.metadata = _read_image_info(grp)
                except Exception:
                    logging.debug("Failed to parse metadata of acquisition '%s'", name)
                    continue

            thumbs.append(da)

    return thumbs

def _dataFromSVIHDF5(f):
    """
    Read microscopy data from an HDF5 file using the SVI convention.
    Expects to find them as IMAGE in XXX/ImageData/Image + XXX/PhysicalData.
    f (h5py.File): the root of the file
    return (list of model.DataArray)
    """
    data = []

    for obj in f.values():
        # find all the expected and interesting objects
        try:
            svidata = obj["SVIData"]
            imagedata = obj["ImageData"]
            image = imagedata["Image"]
            physicaldata = obj["PhysicalData"]
        except KeyError:
            continue # not conforming => try next object

        # Read the raw data
        try:
            da = _read_image_dataset(image)
        except Exception:
            logging.exception("Failed to read data of acquisition '%s'", obj.name)

        # TODO: read more metadata
        try:
            da.metadata.update(_read_image_info(imagedata))
        except Exception:
            logging.exception("Failed to parse metadata of acquisition '%s'", obj.name)
        
        das = _parse_physical_data(physicaldata, da)
        data.extend(das)
    return data

def _dataFromHDF5(filename):
    """
    Read microscopy data from an HDF5 file.
    filename (string): path of the file to read
    return (list of model.DataArray)
    """
    f = h5py.File(filename, "r")

    # if follows SVI convention => use the special function
    # If it has at least one directory like XXX/SVIData => it follows SVI conventions
    for obj in f.values():
        if (isinstance(obj, h5py.Group) and
            isinstance(obj.get("SVIData"), h5py.Group)):
            return _dataFromSVIHDF5(f)

    data = []
    # go rough: return any dataset with numbers (and more than one element)
    def addIfWorthy(name, obj):
        try:
            if not isinstance(obj, h5py.Dataset):
                return
            if not obj.dtype.kind in "biufc":
                return
            if numpy.prod(obj.shape) <= 1:
                return
            # TODO: if it's an image, open it as an image
            # TODO: try to get some metadata?
            da = model.DataArray(obj[...])
        except Exception:
            logging.info("Skipping '%s' as it doesn't seem a correct data", name)
        data.append(da)

    f.visititems(addIfWorthy)
    return data

def _saveAsHDF5(filename, ldata, thumbnail, compressed=True):
    """
    Saves a list of DataArray as a HDF5 (SVI) file.
    filename (string): name of the file to save
    ldata (list of DataArray): list of 2D (up to 5D) data of int or float. 
     Should have at least one array.
    thumbnail (None or DataArray): see export
    compressed (boolean): whether the file is compressed or not.
    """
    # h5py will extend the current file by default, so we want to make sure
    # there is no file at all.
    try:
        os.remove(filename)
    except OSError:
        pass
    f = h5py.File(filename, "w") # w will fail if file exists
    if compressed:
        # szip is not free for commercial usage and lzf doesn't seem to be
        # well supported yet
        compression = "gzip"
    else:
        compression = None

    if thumbnail is not None:
        # Save the image as-is in a special group "Preview"
        prevg = f.create_group("Preview")
        _updateRGBMD(thumbnail) # ensure RGB info is there if needed
        ids = _create_image_dataset(prevg, "Image", thumbnail, compression=compression)
        _add_image_info(prevg, ids, thumbnail)

    # list ndarray/list of list of metadata (one per channel)
    acq, mds = _groupImages(ldata)
    for i, da in enumerate(acq):
        ga = f.create_group("Acquisition%d" % i)
        _add_acquistion_svi(ga, da, mds[i], compression=compression)

    f.close()


# TODO: allow to append data to a file, or any other way to allow saving large
# data without having everything in memory simultaneously.
def export(filename, data, thumbnail=None):
    '''
    Write an HDF5 file with the given image and metadata
    filename (unicode): filename of the file to create (including path)
    data (list of model.DataArray, or model.DataArray): the data to export, 
        must be 2D or more of int or float. Metadata is taken directly from the data 
        object. If it's a list, a multiple page file is created. The order of the
        dimensions is Channel, Time, Z, Y, X. It tries to be smart and if 
        multiple data appears to be the same acquisition at different C, T, Z, 
        they will be aggregated into one single acquisition.
    thumbnail (None or model.DataArray): Image used as thumbnail for the file. Can be of any
      (reasonable) size. Must be either 2D array (greyscale) or 3D with last 
      dimension of length 3 (RGB). If the exporter doesn't support it, it will
      be dropped silently.
    '''
    # TODO: add an argument to not do any clever data aggregation?
    if not isinstance(data, (list, tuple)):
        # TODO should probably not enforce it: respect duck typing
        assert(isinstance(data, model.DataArray))
        data = [data]
    _saveAsHDF5(filename, data, thumbnail)

def read_data(filename):
    """
    Read an HDF5 file and return its content (skipping the thumbnail).
    filename (unicode): filename of the file to read
    return (list of model.DataArray): the data to import (with the metadata 
     as .metadata). It might be empty.
     Warning: reading back a file just exported might give a smaller number of
     DataArrays! This is because export() tries to aggregate data which seems
     to be from the same acquisition but on different dimensions C, T, Z.
     read_data() cannot separate them back explicitly. 
    raises:
        IOError in case the file format is not as expected.
    """
    # TODO: support filename to be a File or Stream (but it seems very difficult
    # to do it without looking at the .filename attribute)
    # see http://pytables.github.io/cookbook/inmemory_hdf5_files.html

    return _dataFromHDF5(filename)

def read_thumbnail(filename):
    """
    Read the thumbnail data of a given HDF5 file.
    filename (unicode): filename of the file to read
    return (list of model.DataArray): the thumbnails attached to the file. If 
     the file contains multiple thumbnails, all of them are returned. If it 
     contains none, an empty list is returned.
    raises:
        IOError in case the file format is not as expected.
    """
    # TODO: support filename to be a File or Stream

    return _thumbFromHDF5(filename)

