import math


def format_size(size):
    prefixes = ['', '*2^10', '*2^20', '*2^30', '*2^40', '*2^50', '*2^60']
    exp = int(math.log(size, 1024))
    exp = min(exp, len(prefixes) - 1)
    return '{:.1f}{} Bytes'.format(size/(1024**exp), prefixes[exp])


def format_duration(seconds):
    if seconds >= 60:
        minutes, seconds = seconds // 60, seconds % 60
        if minutes >= 60:
            hours, minutes = minutes // 60, minutes % 60
            return '{}:{:02d}:{:02d}'.format(hours, minutes, seconds)
        return '{:02d}:{:02d}'.format(minutes, seconds)
    return '00:{:02d}'.format(seconds)
