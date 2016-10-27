def get_spectrum(ds_id, ix, minmz, maxmz, npeaks):
    from pyimzml import ImzMLParser
    import numpy as np
    import os
    import cPickle as pickle
    assert(minmz<maxmz)
    imzml_fname = get_ds_info(ds_id)['imzml']
    imzml_idx_fname = imzml_fname+'.idx'
    if not os.path.exists(imzml_idx_fname):
        imzml_idx = parse_imzml_index(imzml_fname)
        pickle.dump(imzml_idx, open(imzml_idx_fname, 'wb'))
    else:
        imzml_idx = pickle.load(open(imzml_idx_fname, 'rb'))
    mzs, ints = _getspectrum(imzml_idx, open(imzml_idx['bin_filename'], "rb"), ix)
    mzs, ints = np.asarray(mzs), np.asarray(ints)
    lower_ix, upper_ix = np.searchsorted(mzs, minmz), np.searchsorted(mzs, maxmz)
    sort_ix = np.argsort(ints[lower_ix:upper_ix])
    to_return = sort_ix + lower_ix
    if npeaks < len(to_return):
        to_return = to_return[-npeaks:]
    to_return = np.sort(to_return[to_return < len(ints)])
    mzs = mzs[to_return]
    ints = ints[to_return]
    return mzs, ints

def get_image(ds_id, mz, ppm):
    from cpyImagingMSpec import ImzbReader
    print mz, ppm
    imzb_fname = get_ds_info(ds_id)['imzb']
    imzb = ImzbReader(imzb_fname)
    ion_image = imzb.get_mz_image(mz, ppm)
    return ion_image

ds_info = {
    '0': {
        'name': '12hour_5_210',
        'imzml': '/home/palmer/Documents/tmp_data/test_dataset/12hour_5_210_centroid.imzML',
        'imzb': '/home/palmer/Documents/tmp_data/test_dataset/12hour_5_210_centroid.imzb'
    },

}
def get_ds_info(id):
    # todo reimplement this in database
    # quick hack -> this will go into the database
    return ds_info[id]

def get_ds_name(ds_id):
    return get_ds_info(ds_id)['name']


def get_all_dataset_names_and_ids():
    ds_ids = ds_info.keys()
    ds_names = [ds_info[k]['name'] for k in ds_ids]
    return ds_names, ds_ids


def b64encode(im_vect, im_shape):
    import base64
    import matplotlib.pyplot as plt
    import numpy as np
    import StringIO
    in_memory_path  = StringIO.StringIO()
    plt.imsave(in_memory_path, np.reshape(im_vect, im_shape))
    encoded = base64.b64encode(in_memory_path.getvalue())
    return encoded

def coord_to_ix(ds_id, x, y):
    from pyimzml import ImzMLParser
    import numpy as np
    imzml_fname = get_ds_info(ds_id)['imzml']
    imzml = ImzMLParser.ImzMLParser(imzml_fname)
    print x, y
    ix = np.where([all([c[0]==x, c[1]==y]) for c in imzml.coordinates])[0][0]
    return ix

def parse_imzml_index(imzml_filename):
    from pyimzml import ImzMLParser
    imzml = ImzMLParser.ImzMLParser(imzml_filename)
    imzml_idx = {'bin_filename': imzml.filename[:-5] + "ibd",
                 'mzOffsets': imzml.mzOffsets,
                 'mzLengths': imzml.mzLengths,
                 'intensityOffsets': imzml.intensityOffsets,
                 'intensityLengths': imzml.intensityLengths,
                 'sizeDict': imzml.sizeDict,
                 'mzPrecision': imzml.mzPrecision,
                 'intensityPrecision': imzml.intensityPrecision,
                 }
    return imzml_idx


def _get_spectrum_as_string(imzml_idx, m, index):
    """
    Reads m/z array and intensity array of the spectrum at specified location
    from the binary file as a byte string. The string can be unpacked by the struct
    module. To get the arrays as numbers, use getspectrum
    :param index:
        Index of the desired spectrum in the .imzML file
    :rtype: Tuple[str, str]
    Output:
    mz_string:
        string where each character represents a byte of the mz array of the
        spectrum
    intensity_string:
        string where each character represents a byte of the intensity array of
        the spectrum
    """
    offsets = [imzml_idx['mzOffsets'][index], imzml_idx['intensityOffsets'][index]]
    lengths = [imzml_idx['mzLengths'][index], imzml_idx['intensityLengths'][index]]
    lengths[0] *= imzml_idx['sizeDict'][imzml_idx['mzPrecision']]
    lengths[1] *= imzml_idx['sizeDict'][imzml_idx['intensityPrecision']]
    m.seek(offsets[0])
    mz_string = m.read(lengths[0])
    m.seek(offsets[1])
    intensity_string = m.read(lengths[1])
    return mz_string, intensity_string


def _getspectrum(imzml_idx, m, index):
    """
    Reads the spectrum at specified index from the .ibd file.
    :param index:
        Index of the desired spectrum in the .imzML file
    Output:
    mz_array:
        Sequence of m/z values representing the horizontal axis of the desired mass
        spectrum
    intensity_array:
        Sequence of intensity values corresponding to mz_array
    """
    import struct
    mz_string, intensity_string = _get_spectrum_as_string(imzml_idx, m, index)
    mz_fmt = '<' + str(int(len(mz_string) / imzml_idx['sizeDict'][imzml_idx['mzPrecision']])) + imzml_idx['mzPrecision']
    intensity_fmt = '<' + str(
        int(len(intensity_string) / imzml_idx['sizeDict'][imzml_idx['intensityPrecision']])) + imzml_idx['intensityPrecision']
    mz_array = struct.unpack(mz_fmt, mz_string)
    intensity_array = struct.unpack(intensity_fmt, intensity_string)
    return mz_array, intensity_array