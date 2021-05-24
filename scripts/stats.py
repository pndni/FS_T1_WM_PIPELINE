from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ArgumentError
import sys
import os
from os.path import join, split
import traceback
import time
import pandas as pd
import SimpleITK as sitk
from scipy import stats
import numpy as np

measures = ['mean', 'std', 'skew', 'kurtosis', 'min', 'max', 'nVox']


def resample_mask2ref(mask, refImg):
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(refImg)
    resample.SetDefaultPixelValue(0)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    resample.AddCommand(sitk.sitkProgressEvent,
                        lambda: sys.stdout.flush())
    msk_resampled = resample.Execute(mask)
    return msk_resampled


def check_exist(*args):
    for arg in args:
        if arg is None:
            continue
        if not os.path.isfile(arg):
            raise Exception(f"{arg} file does not exist")


def img_compare(img1, img2, v=1):
    round_tpl = lambda tpl, n: tuple(round(x, n) for x in tpl)
    size_1 = img1.GetSize()
    size_2 = img2.GetSize()
    spacing_1 = img1.GetSpacing()
    spacing_2 = img2.GetSpacing()
    origin_1 = img1.GetOrigin()
    origin_2 = img2.GetOrigin()
    direction_1 = img1.GetDirection()
    direction_2 = img2.GetDirection()

    if v:
        print('size: \n img 1 {} \n img 2 {}'.format(round_tpl(size_1, 6),
                                                     round_tpl(size_2, 6)))
        print('spacing: \n img 1 {} \n img 2 {}'.format(round_tpl(spacing_1, 6),
                                                        round_tpl(spacing_2, 6)))
        print('origin: \n img 1 {} \n img 2 {}'.format(round_tpl(origin_1, 6),
                                                       round_tpl(origin_2, 6)))
        print('direction: \n img 1 {} \n img 2 {}'.format(round_tpl(direction_1, 6),
                                                          round_tpl(direction_2, 6)))
    same_size = np.allclose(size_1, size_2), 
    same_spacing = np.allclose(spacing_1, spacing_2)
    same_origin = np.allclose(origin_1, origin_2)
    same_direction = np.allclose(direction_1, direction_2)
    same = same_size and same_spacing and same_origin and same_direction
    if v:
        print(f"equivalent: {same}")
        if not same_size:
            print("Size missmatch {} not same as {}".format(size_1, size_2))
        if not same_spacing:
            print("Spacing missmatch {} not same as {}".format(spacing_1, spacing_2))
        if not same_origin:
            print("Origin missmatch {} not same as {}".format(origin_1, origin_2))
        if not same_direction:
            print("Direction missmatch {} not same as {}".format(direction_1, direction_2))
    return same


def resample_mask2ref(mask, refImg):
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(refImg)
    resample.SetDefaultPixelValue(0)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    resample.AddCommand(sitk.sitkProgressEvent,
                        lambda: sys.stdout.flush())
    msk_resampled = resample.Execute(mask)
    return msk_resampled


def img_norm(img_arr):
    img_arr_norm = img_arr - img_arr.min()
    img_arr_norm = img_arr_norm / img_arr_norm.max()
    assert(img_arr_norm.min() == 0)
    assert(img_arr_norm.max() == 1)
    return img_arr_norm


def assert_is_binary_mask(msk_arr):
    mini = msk_arr.min()
    assert mini == 0, f"Min Error {mini}"
    maxi = msk_arr.max()
    assert maxi <= 1, f"Max Error {maxi}"
    uniq = np.unique(msk_arr)
    assert len(uniq) <= 2, f"Unique values error {uniq}"

def resample_to_IMG(IMG, WM, GM, CM, SM, BM):
    ref_img = IMG
    resampled_masks = []
    for msk in [WM, GM, CM, SM, BM]:
        if msk is None:
            resampled_masks.append(None)
            continue
        if not img_compare(msk, ref_img, v=True):
            msk = resample_mask2ref(msk, ref_img)
        resampled_masks.append(msk)
    return tuple(resampled_masks)


def load_data(IMG_path, WM_path, GM_path, CM_path, SM_path, BM_path):
    IMG = sitk.ReadImage(IMG_path)
    if WM_path is not None:
        WM = sitk.ReadImage(WM_path)
    else:
        WM = None
    if GM_path is not None:
        GM = sitk.ReadImage(GM_path)
    else:
        GM = None
    if CM_path is not None:
        CM = sitk.ReadImage(CM_path)
    else:
        CM = None
    SM = sitk.ReadImage(SM_path)
    BM = sitk.ReadImage(BM_path)
    return IMG, WM, GM, CM, SM, BM


def get_arrays(IMG, WM, GM, CM, SM, BM):
    IMG_arr = sitk.GetArrayFromImage(IMG)
    if WM is not None:
        WM_arr = sitk.GetArrayFromImage(WM)
        assert_is_binary_mask(WM_arr)
    else:
        WM_arr = None
    if GM is not None:
        GM_arr = sitk.GetArrayFromImage(GM)
        assert_is_binary_mask(GM_arr)
    else:
        GM_arr = None
    if CM is not None:
        CM_arr = sitk.GetArrayFromImage(CM)
        assert_is_binary_mask(CM_arr)
    else:
        CM_arr = None
    SM_arr = sitk.GetArrayFromImage(SM)
    BM_arr = sitk.GetArrayFromImage(BM)
    assert_is_binary_mask(BM_arr)
    
    return IMG_arr, WM_arr, GM_arr, CM_arr, SM_arr, BM_arr


def check_img_consistent(IMG, WM, GM, SM, BM, v=0):
    ref_img = IMG
    for img in [WM, GM, SM, BM]:
        if img is None:
            continue
        assert img_compare(ref_img, img, v=v)


def get_cerebrum_mask(SM_arr, BM_arr, ref_df):
    print(type(SM_arr), type(BM_arr), type(ref_df))
    SM_arr2 = SM_arr * BM_arr
    CM_arr = SM_arr2.copy()
    if 'cerebrum' not in ref_df.columns:
        return None
    non_cerebrum_lbls = ref_df[~ref_df['cerebrum']].index.values
    for lbl in non_cerebrum_lbls:
        CM_arr[CM_arr == lbl] = 0
    CM_arr = CM_arr > 0
    return CM_arr, SM_arr2


def get_masked_stats(img_array, mask_array):
    if mask_array.sum() == 0:
        return {m: np.NaN for m in measures}
    masked_img = img_array[np.where(mask_array)]
    summary_stats = stats.describe(masked_img.ravel())
    nobs, minmax, mean, var, skew, kurtosis = summary_stats
    stats_dict = {'mean': mean, 'min': minmax[0], 'nVox': nobs,
                  'max': minmax[1], 'skew': skew, 'kurtosis': kurtosis}
    stats_dict['std'] = np.sqrt(var)
    return stats_dict


def get_stats(IMG_arr, SM_arr, ref_df, BM_arr, 
              row_tag, CM_arr=None,
              TM_arr=None, cerebrum_only=False, 
              vox_vol=None, save_path=None):

    if 'cerebrum' in ref_df.columns and cerebrum_only:
        cerebrum_idx = ref_df['cerebrum']
        labels = list(ref_df[cerebrum_idx].index.values)
        lobes = list(ref_df[cerebrum_idx]['label_name'].values)
        non_cerebrum_lbls = ref_df[~cerebrum_idx].index.values
    else:
        labels = list(ref_df.index.values)
        lobes = list(ref_df['label_name'].values)
        non_cerebrum_lbls = []
        #assert np.alltrue(np.sort([0]+labels) == np.sort(np.unique(SM_arr))), "labels {}, atlas lbls {}".format(labels, np.unique(SM_arr))
    
    stats_df = pd.DataFrame(index=lobes, columns=measures)
    if TM_arr is not None:
        SM_arr = SM_arr * TM_arr
    for lbl in labels:
        if lbl in non_cerebrum_lbls:
            continue
        lobe = ref_df.loc[lbl]['label_name']
        print('\t label {}, lobe {}'.format(lbl, lobe))
        SM_mask_i = SM_arr == lbl
        assert_is_binary_mask(SM_mask_i)
        assert(IMG_arr.shape == SM_mask_i.shape)
        stats_dict = get_masked_stats(IMG_arr, SM_mask_i)
        for m in measures:
            print('\t \t {}: {}'.format(m, stats_dict[m]))
            stats_df.loc[lobe, m] = stats_dict[m]
    # Cerebrum stats
    if CM_arr is not None:
        if TM_arr is not None:
            CM_arr_ = CM_arr * TM_arr
        else:
            CM_arr_ = CM_arr
        stats_dict = get_masked_stats(IMG_arr, CM_arr_)
        print('\t Cerebrum')
        for m in measures:
            print('\t \t {}: {}'.format(m, stats_dict[m]))
            stats_df.loc['Cerebrum', m] = stats_dict[m]
    # Full Brain
    if not cerebrum_only:
        if TM_arr is not None:
            BM_arr_ = BM_arr * TM_arr
        else:
            BM_arr_ = BM_arr
        stats_dict = get_masked_stats(IMG_arr, BM_arr_)
        print('\t Brain')
        for m in measures:
            print('\t \t {}: {}'.format(m, stats_dict[m]))
            stats_df.loc['Brain', m] = stats_dict[m]
        # volume
        if vox_vol is not None:
            stats_df['volume [mm^3]'] = vox_vol * stats_df['nVox']
        # Save
    stats_df.index.name = 'Region'
    stats_df.index = row_tag + "_" + stats_df.index
    if save_path is not None:
        stats_df.to_csv(save_path)


def save_masks(ref_img, WM_arr, GM_arr, CM_arr, SM_arr2, BM_arr, outdir, tag):
    if WM_arr is not None:
        WM = sitk.GetImageFromArray(WM_arr)
        WM.CopyInformation(ref_img)
        sitk.WriteImage(WM, join(outdir, 'WhiteMatterMask.nii.gz'))

    if GM_arr is not None:
        GM = sitk.GetImageFromArray(GM_arr)
        GM.CopyInformation(ref_img)
        sitk.WriteImage(GM, join(outdir, 'GrayMatterMask.nii.gz'))

    if CM_arr is not None:
        CM = sitk.GetImageFromArray(CM_arr)
        CM.CopyInformation(ref_img)
        sitk.WriteImage(CM, join(outdir, 'CerebrumMask.nii.gz'))

    SM = sitk.GetImageFromArray(SM_arr2) # Label / Segmentation Mask
    SM.CopyInformation(ref_img)
    sitk.WriteImage(SM, join(outdir, f"LabelMask_{tag}.nii.gz"))

    BM = sitk.GetImageFromArray(BM_arr)
    BM.CopyInformation(ref_img)
    sitk.WriteImage(BM, join(outdir, 'BrainMask.nii.gz'))


def main(IMG_path, WM_path, GM_path, CM_path, SM_path, BM_path, 
         ref_file, outdir, tag, debug):
    if not(os.path.isdir(outdir)):
        os.makedirs(outdir)
    check_exist(IMG_path, WM_path, GM_path, CM_path, SM_path, BM_path, ref_file)
    IMG, WM, GM, CM, SM, BM = load_data(IMG_path, WM_path, GM_path, CM_path, SM_path, BM_path)
    ref_df = pd.read_csv(ref_file, index_col=0)
    WM, GM, CM, SM, BM = resample_to_IMG(IMG, WM, GM, CM, SM, BM)
    check_img_consistent(IMG, WM, GM, CM, SM, BM)
    IMG_arr, WM_arr, GM_arr, CM_arr, SM_arr, BM_arr = get_arrays(IMG, WM, GM, CM, SM, BM)
    SM_arr2 = SM_arr * BM_arr # Refine segmentation mask - all labels inside brain
    
    spacing = IMG.GetSpacing()
    vox_vol = np.prod(spacing)
    print("\t GETTING ALL STATS...")
    get_stats(IMG_arr, SM_arr2, ref_df, BM_arr, 
              row_tag="ALL", CM_arr=CM_arr,
              TM_arr=None, vox_vol=vox_vol, 
              save_path=join(outdir, f"ALL_stats_{tag}.csv"))
    if WM_arr is not None:
        print("\t GETTING WM STATS...")
        get_stats(IMG_arr, SM_arr2, ref_df, BM_arr,
                row_tag="WM", CM_arr=CM_arr,
                TM_arr=WM_arr, vox_vol=vox_vol,
                save_path=join(outdir, f"WM_stats_{tag}.csv"))
    if GM_arr is not None:
        print("\t GETTING GM STATS...")
        get_stats(IMG_arr, SM_arr2, ref_df, BM_arr,
                row_tag="GM", CM_arr=CM_arr,
                TM_arr=GM_arr, vox_vol=vox_vol, cerebrum_only=True,
                save_path=join(outdir, f"GM_stats_{tag}.csv"))
    save_masks(IMG, WM_arr, GM_arr, CM_arr, SM_arr2, BM_arr, outdir, tag)


def get_parser():
    module_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    module_parser.add_argument("-i", dest="I", type=str,
                               help="Input image")
    module_parser.add_argument("-WM", dest="WM", type=str, default=None,
                               help="WM mask path")
    module_parser.add_argument("-GM", dest="GM", type=str, default=None,
                               help="GM mask path")
    module_parser.add_argument("-CM", dest="CM", type=str, default=None,
                               help="Cerebrum mask path")
    module_parser.add_argument("-SM", dest="SM", type=str,
                               help="Segmentation mask path (lobes/DK)")
    module_parser.add_argument("-BM", dest="BM", type=str,
                               help="Brain mask path")
    module_parser.add_argument("-r", dest="ref", type=str,
                               help="reference table for segmentation")
    module_parser.add_argument("-o", dest="outdir", type=str,
                               help="Output directory path")
    module_parser.add_argument("-t", dest="tag", type=str,
                               help="info tag")
    module_parser.add_argument("-debug", dest="debug", type=int, default=0,
                               help="DEBUG MODE [1 - ON, 0 - OFF (default: 0)]")
    return module_parser


if __name__ == "__main__":
    t0 = time.time()
    parser = get_parser()
    try:
        args = parser.parse_args()
        main(args.I,
             args.WM,
             args.GM,
             args.CM,
             args.SM,
             args.BM,
             args.ref,
             args.outdir,
             args.tag,
             args.debug)
    except ArgumentError as arg_exception:
        traceback.print_exc()
    except Exception as exception:
        traceback.print_exc()
    dt = (time.time() - t0) / 60
    print('done... python script runtime: {} min'.format(dt))
    sys.exit()
