import string
import numpy as np
import os
import sys
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import scipy.io


class TF:
    def __init__(self, f_id, cf_id):
        self.frame_id = f_id
        self.child_frame_id = cf_id


# loads all CSVs in a directory and stores them as a .mat
def main():
    data_dir = sys.argv[1]
    for data_file in os.listdir(data_dir):
        if data_file.endswith('.csv'):
            csv_to_mat(data_dir, data_file)
    # mat_to_csv(data_dir, data_file)

    return


def csv_to_mat(data_dir, data_file):
    print "Loading from file: " + data_dir + "/" + data_file

    data, time_sec, time_nsec, image_id, tf_ordering = load_csv(data_dir + "/" + data_file)

    times = np.vstack((time_sec, time_nsec))
    times = np.vstack((times, image_id))
    times = np.transpose(times)

    write_mat(data_dir, data_file, data, times, tf_ordering)

    print "Wrote to .mats with %i samples and %i features" % data.shape


def mat_to_csv(data_dir, data_base):
    data_file = data_dir + data_base + '_data_reconstructed.mat'

    # cheat and use the same times, image_ids, and tfs as the original CSV so we only load the data mat
    data, time_sec, time_nsec, image_id, tf_ordering = load_csv(data_dir + data_base + '.csv')

    data = scipy.io.loadmat(data_file)

    write_csv(data_dir + data_base + '_reconstructed.csv', data['reconstructed_data'], tf_ordering, time_sec,
              time_nsec, image_id)


# loads a CSV into a numpy matrix, ignores any tf with strings in ignored_children as their child_frame_id
# and ignores any tf with strings in ignored_parents as their frame_id (in the csv the format is frame_id,
# child_framed_id)
def load_csv(file):
    # treat the tf identifiers as comments, ignore
    loaded = np.loadtxt(file, dtype='str', delimiter=',')

    num_cols = 0
    num_rows = loaded.shape[0]
    # count the number of usable columns to preallocate, skip first three (times + image_id)
    for i in range(3, loaded.shape[1]):
        if is_float_cell(loaded[0, i]):
            # print loaded[0, i]
            num_cols += 1

    # preallocate and fill data matrix
    data = np.zeros((num_rows, num_cols))
    column = np.zeros((num_rows, 1), dtype='|S16')
    j = 0
    tf_ordering = [] # stores array of tf's in order of the original file
    # first 3 entries are time_s, time_ns, image_id
    time_sec = np.array(loaded[:, 0], dtype=int)
    time_nsec = np.array(loaded[:, 1], dtype=int)
    image_id = np.array(loaded[:, 2], dtype=int)
    i = 3
    data_idx = 0
    while i < loaded.shape[1]:
        entry_type, tf_ordering = check_entry(loaded, i, tf_ordering)
        if entry_type == 'tf':
            for j in range(i+2, i+9):
                column = loaded[:, j]
                data[:, data_idx] = np.array(column)
                data_idx += 1
            i += 9
        elif entry_type == 'force':
            for j in range(i, i+26):
                data[:, data_idx] = np.array(loaded[:, j])
                data_idx += 1
            break # finished after force

    return data, time_sec, time_nsec, image_id, tf_ordering


def check_entry(loaded, col, tf_ordering):
    # check if cell is a tf
    cell = loaded[0, col]
    if loaded[0, col][0].isalpha() or loaded[0, col][0] == '/':
        tf_ordering.append(TF(loaded[0, col], loaded[0, col+1]))
        return 'tf', tf_ordering
    else:
        return 'force', tf_ordering


def write_mat(dir, fname, data, times, tfs):
    scipy.io.savemat(dir + "/" + fname + '_data.mat', mdict={'data': data})
    scipy.io.savemat(dir + "/" + fname + '_times.mat', mdict={'times': times})
    scipy.io.savemat(dir + "/" + fname + '_tf_order.mat', mdict={'tfs': tfs})


def load_mat(dir, datafname):
    data = scipy.io.loadmat(dir + datafname)

    return data


def write_csv(filename, data, tf_ordering, time_sec, time_nsec, image_id):
    # construct array with all data
    write_arr = np.empty(shape=(data.shape[0], 3 + data.shape[1] + 2 * len(tf_ordering)), dtype=object)
    write_arr[:, 0] = time_sec
    write_arr[:, 1] = time_nsec
    write_arr[:, 2] = image_id
    data_idx = 0
    write_idx = 3
    for tf_idx in range(0, len(tf_ordering)):
        # write tf
        write_arr[:, write_idx] = np.full((data.shape[0]), tf_ordering[tf_idx].frame_id, dtype=object)
        write_idx += 1
        write_arr[:, write_idx] = np.full((data.shape[0]), tf_ordering[tf_idx].child_frame_id, dtype=object)
        write_idx += 1
        print "tf_idx: %i Writing tf %s -> %s" % (tf_idx, tf_ordering[tf_idx].frame_id, tf_ordering[
            tf_idx].child_frame_id)
        # write the next 7 columns
        for j in range(0, 7):
            write_arr[:, write_idx] = data[:, data_idx]
            print "tf_idx: %i w_idx: %i d_idx: %i" % (tf_idx, write_idx, data_idx)
            data_idx += 1
            write_idx += 1
    # write remaining forces
    for i in range(data_idx, data.shape[1]):
        write_arr[:, write_idx] = data[:, data_idx]
        data_idx += 1
        write_idx += 1
    # actually write the file
    np.savetxt(filename, write_arr, delimiter=',', fmt='%s')


# determines if a string cell contains a floating point number (not robustly!)
def is_float_cell(cell):
    return len(cell) > 0 and (cell[0].isdigit() or cell[0] == '-')


if __name__ == "__main__":

    # times = scipy.io.loadmat('/home/mark/Dropbox/Documents/SIMPLEX/DataCollection/11_29_data_local/glovedata/pca'
    #                  '/hand_only_csvs/bottle64_palm/bottle64_open_palm_success_corrected_order8-12-13_times'
    #                          '.mat')

    main()
