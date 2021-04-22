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


label_names={}
label_names[1]='Frontal_rh'
label_names[2]='Parietal_rh'
label_names[3]='Temporal_rh'
label_names[4]='Occipital_rh'
label_names[5]='Frontal_lh'
label_names[6]='Parietal_lh'
label_names[7]='Temporal_lh'
label_names[8]='Occipital_lh'
label_names[9]='Cerebellum_lh'
label_names[10]='Sub-cortical_lh'
label_names[11]='Brainstem_lh'
label_names[12]='Cerebellum_rh'
label_names[13]='Sub-cortical_rh'
label_names[14]='Brainstem_rh'

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


def get_masked_stats(img_array, mask_array):
    masked_img = img_array[np.where(mask_array)]
    summary_stats = stats.describe(masked_img.ravel())
    nobs, minmax, mean, var, skew, kurtosis = summary_stats
    stats_dict = {'mean': mean, 'min': minmax[0], 'nVox': nobs,
                  'max': minmax[1], 'skew': skew, 'kurtosis': kurtosis}
    stats_dict['std'] = np.sqrt(var)
    return stats_dict


def get_mask_array(msk):
    if type(msk) is str:
        msk = sitk.ReadImage(msk)
    msk_arr = sitk.GetArrayFromImage(msk)
    assert(len(np.unique(msk_arr)) == 2)
    assert(msk_arr.min() == 0)
    assert(msk_arr.max() == 1)
    return msk_arr


def img_norm(img_arr):
    img_arr_norm = img_arr - img_arr.min()
    img_arr_norm = img_arr_norm / img_arr_norm.max()
    assert(img_arr_norm.min() == 0)
    assert(img_arr_norm.max() == 1)
    return img_arr_norm


def check_exist(T1, WM, GM, LB, BM):
    assert os.path.isfile(T1), 'T1 does not exist {}'.format(T1)
    assert os.path.isfile(WM), 'WM does not exist {}'.format(WM)
    assert os.path.isfile(GM), 'GM does not exist {}'.format(GM)
    assert os.path.isfile(LB), 'LB does not exist {}'.format(LB)
    assert os.path.isfile(BM), 'T1 does not exist {}'.format(BM)


def load_images(T1_path, WM_path, GM_path, LB_path, BM_path):
    T1 = sitk.ReadImage(T1_path)
    WM = sitk.ReadImage(WM_path)
    GM = sitk.ReadImage(GM_path)
    LB = sitk.ReadImage(LB_path)
    BM = sitk.ReadImage(BM_path)
    return T1, WM, GM, LB, BM


def get_stats(T1_arr, WM_arr, GM_arr, LB_arr, ctx_arr):
    labels = list(label_names.keys())
    lobes = label_names.values()
    assert np.alltrue(np.sort([0]+labels) == np.sort(np.unique(LB_arr))), "labels {}, atlas lbls {}".format(labels, np.unique(LB_arr))
    stats_df_wm = pd.DataFrame(index=lobes, columns=measures)
    stats_df_gm = pd.DataFrame(index=lobes, columns=measures)
    for lbl in labels:
        lobe = label_names[lbl]
        print('\t label {}, lobe {}'.format(lbl, lobe))
        LB_mask_i = LB_arr == lbl
        WM_mask_i = WM_arr * LB_mask_i
        GM_mask_i = GM_arr * LB_mask_i
        assert_is_binary_mask(WM_mask_i)
        assert_is_binary_mask(GM_mask_i)
        assert(T1_arr.shape == WM_mask_i.shape)
        assert(T1_arr.shape == GM_mask_i.shape)
        stats_dict_wm = get_masked_stats(T1_arr, WM_mask_i)
        stats_dict_gm = get_masked_stats(T1_arr, GM_mask_i)
        for m in measures:
            print('\t \t {} WM: {}'.format(m, stats_dict_wm[m]))
            stats_df_wm.loc[lobe, m] = stats_dict_wm[m]
            print('\t \t {} GM: {}'.format(m, stats_dict_gm[m]))
            stats_df_gm.loc[lobe, m] = stats_dict_gm[m]
    # Whole Brain Stats
    print('\t Cortex')
    WM_ctx = WM_arr * ctx_arr
    GM_ctx = GM_arr * ctx_arr
    
    stats_dict_wm = get_masked_stats(T1_arr, WM_ctx)
    stats_dict_gm = get_masked_stats(T1_arr, GM_ctx)
    for m in measures:
        print('\t \t {} WM: {}'.format(m, stats_df_wm[m]))
        stats_df_wm.loc['Cortex', m] = stats_dict_wm[m]
        print('\t \t {} GM: {}'.format(m, stats_df_gm[m]))
        stats_df_gm.loc['Cortex', m] = stats_dict_gm[m]
    return stats_df_wm, stats_df_gm


def assert_is_binary_mask(msk_arr):
    assert(len(np.unique(msk_arr)) == 2)
    assert(msk_arr.min() == 0)
    assert(msk_arr.max() == 1)


def get_arrays(T1, WM, GM, LB, BM):
    T1_arr = sitk.GetArrayFromImage(T1)
    WM_arr = sitk.GetArrayFromImage(WM)
    GM_arr = sitk.GetArrayFromImage(GM)
    LB_arr = sitk.GetArrayFromImage(LB)
    BM_arr = sitk.GetArrayFromImage(BM)
    assert_is_binary_mask(WM_arr)
    assert_is_binary_mask(GM_arr)
    return T1_arr, WM_arr, GM_arr, LB_arr, BM_arr


def resample_to_T1(T1, WM, GM, LB, BM):
    ref_img = T1
    resampled_masks = []
    for msk in [WM, GM, LB, BM]:
        if not img_compare(msk, ref_img, v=True):
            msk = resample_mask2ref(msk, ref_img)
        resampled_masks.append(msk)
    return resampled_masks[0], resampled_masks[1], resampled_masks[2], resampled_masks[3]


def check_img_consistent(T1, WM, GM, LB, BM, v=0):
    ref_img = T1
    for img in [WM, GM, LB, BM]:
        assert img_compare(ref_img, img, v=v)


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


def save_masks(WM, GM, LB, BM, CTX, outdir):
    sitk.WriteImage(LB, join(outdir, 'Lobe_mask.nii.gz'))
    sitk.WriteImage(BM, join(outdir, 'Brain_mask.nii.gz'))
    sitk.WriteImage(WM, join(outdir, 'WhiteMatter_mask.nii.gz'))
    sitk.WriteImage(GM, join(outdir, 'GrayMatter_mask.nii.gz'))
    sitk.WriteImage(CTX, join(outdir, 'cortex_mask.nii.gz'))


def main(T1_path, WM_path, GM_path, LB_path, BM_path, outdir, debug):
    if not(os.path.isdir(outdir)):
        os.makedirs(outdir)
    check_exist(T1_path, WM_path, GM_path, LB_path, BM_path)
    T1, WM, GM, LB, BM = load_images(T1_path, WM_path, GM_path, LB_path, BM_path)
    WM, GM, LB, BM = resample_to_T1(T1, WM, GM, LB, BM)
    print("****** WM {}, GM {}, LB {}, BM {}".format(WM.GetSize(),
                                                     GM.GetSize(), 
                                                     LB.GetSize(), 
                                                     BM.GetSize()))
    check_img_consistent(T1, WM, GM, LB, BM)
    T1_arr, WM_arr, GM_arr, LB_arr, BM_arr = get_arrays(T1, WM, GM, LB, BM)

    LB_arr2 = LB_arr * BM_arr
    ctx_arr = np.copy(LB_arr2)
    ctx_arr[ctx_arr > 8] = 0  # suppress subcortical regions
    ctx_arr = ctx_arr > 0  # binarize volume

    stats_df_wm, stats_df_gm = get_stats(T1_arr, WM_arr, GM_arr, LB_arr2, ctx_arr)
    stats_df_wm.index.name = 'Lobe'
    stats_df_gm.index.name = 'Lobe'
    stats_df_wm.to_csv(join(outdir, "WM_stats.csv"))
    stats_df_gm.to_csv(join(outdir, "GM_stats.csv"))

    T1_arr_norm = img_norm(T1_arr)
    norm_stats_df_wm, norm_stats_df_gm = get_stats(T1_arr_norm, WM_arr, GM_arr, LB_arr2, ctx_arr)
    norm_stats_df_wm.index.name = 'Lobe'
    norm_stats_df_gm.index.name = 'Lobe'
    norm_stats_df_wm.to_csv(join(outdir, "WM_stats_norm.csv"))
    norm_stats_df_gm.to_csv(join(outdir, "GM_stats_norm.csv"))

    # save masks
    CTX = sitk.GetImageFromArray(ctx_arr.astype(np.uint8))
    CTX.CopyInformation(T1)
    save_masks(WM, GM, LB, BM, CTX, outdir)


def get_parser():
    module_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    module_parser.add_argument("-i", dest="Img", type=str,
                               help="Input image")
    module_parser.add_argument("-WM", dest="WM", type=str,
                               help="WM mask path")
    module_parser.add_argument("-GM", dest="GM", type=str,
                               help="GM mask path")
    module_parser.add_argument("-LM", dest="LB", type=str,
                               help="Lobe mask path")
    module_parser.add_argument("-BM", dest="BM", type=str,
                               help="Brain mask path")
    module_parser.add_argument("-o", dest="outdir", type=str,
                               help="Output directory path")
    module_parser.add_argument("-debug", dest="debug", type=int, default=0,
                               help="DEBUG MODE [1 - ON, 0 - OFF (default: 0)]")
    return module_parser


if __name__ == "__main__":
    t0 = time.time()
    parser = get_parser()
    try:
        args = parser.parse_args()
        main(args.Img,
             args.WM,
             args.GM,
             args.LB,
             args.BM,
             args.outdir,
             args.debug)
    except ArgumentError as arg_exception:
        traceback.print_exc()
    except Exception as exception:
        traceback.print_exc()
    dt = (time.time() - t0) / 60
    print('done... python script runtime: {} min'.format(dt))
    sys.exit()
