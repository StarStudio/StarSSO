
def table_print(_data, _limits, _margin):
    '''
        Print table line with specfied format.
        _data       line of data elements to print
        _limits     box size of elements
        _margin     margin between two boxes.
    '''
    if not isinstance(_data, list):
        if isinstance(_data, tuple):
            _data = list(_data)
        else:
            raise TypeError('_dict should be list or tuple')
    if not isinstance(_limits, list) and not isinstance(_limits, tuple):
        raise TypeError('_limits should be list or tuple')
    if len(_data) != len(_limits):
        raise ValueError('_limits should have same length with _dict.')

    idx_vec = [0 for i in range(0, len(_data))]
    len_vec = []
    #Convert all elements to string
    for idx in range(0, len(_data)):
        if str == type(_data[idx]):
            _data[idx] = '%s' % _data[idx]
        elif int == type(_data[idx]):
            _data[idx] = '%d' % _data[idx]
        else:
            raise TypeError('Unsupport element type: %s' % type(_data[idx]).__name__)
            return False
        len_vec.append(len(_data[idx]))

    end = False
    while not end:
        # loop for all elements
        end = True
        for idx in range(0, len(_data)):
            # element is fully printed. so just add padding
            if len_vec[idx] <= idx_vec[idx]:
                print(' '*(_limits[idx] + _margin[idx]), end = '')
                continue
            # calculate used spaces
            occup = 0 ; ldx = idx_vec[idx]; nidx = -1
            while occup < _limits[idx] and ldx < len_vec[idx]:
                # drawback : chinese character only
                cord = ord(_data[idx][ldx])
                if 0x4e00 < cord and cord < 0x9fa5:
                    if occup + 2 > _limits[idx]:
                        break
                    occup += 2
                elif _data[idx][ldx] == '\n':
                    nidx = ldx
                    break
                else:
                    occup += 1
                ldx += 1
            # If newline is found (\n), cut the string.
            if nidx != -1:
                print('%s' % _data[idx][idx_vec[idx]:nidx] + ' '*(_limits[idx] - occup), end = '')
                ldx = nidx + 1
            # If box cannot contain the remain part, cut and squeeze it to next line.
            else:
                print('%s' % _data[idx][idx_vec[idx]: ldx] + ' '*(_limits[idx] - occup), end = '')
            # loop until all elements are fully printed
            if ldx < len_vec[idx]:
                end = False
            idx_vec[idx] = ldx
            # pad with margin blanks
            print(' ' * _margin[idx], end = '')
        # next line
        print('')

    return True
