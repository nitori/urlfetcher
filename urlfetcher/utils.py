__author__ = 'Nitori'


def format_size(size):
    prefixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']
    scale = 1024
    for i, prefix in enumerate(prefixes):
        if size < scale**(i+1):
            return '{:.1f} {}'.format(size/(scale**i), prefix)
    return '{:.1f} {}'.format(size/(scale**i), prefix)


def format_duration(seconds):
    if seconds >= 60:
        minutes, seconds = seconds // 60, seconds % 60
        if minutes >= 60:
            hours, minutes = minutes // 60, minutes % 60
            return '{}:{:02d}:{:02d}'.format(hours, minutes, seconds)
        return '{:02d}:{:02d}'.format(minutes, seconds)
    return '00:{:02d}'.format(seconds)
