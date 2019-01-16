from chardet.universaldetector import UniversalDetector  # pip install chardet
import io
import os.path


def open(file, mode='r', buffering=-1, encoding=None, errors=None,
         newline=None, closefd=True):
    """ A wrapper for io.open(), which tries to detect the encoding of a file
    using chardet before reading or writing

    Supports all arguments of io.open(). "encoding" is only used if file does
    not exist.

    Binary mode is not supported.

    Usage:

    >>> import chardet_open
    >>> my_fh = chardet_open.open('french-iso.txt', mode="r+")
    >>> print my_fh.encoding
    ISO-8859-1
    >>> print my_fh.read()
    Wikipédia est un projet dencyclopédie...
    """

    if 'b' in mode:
        raise Exception("binary mode not supported")

    if os.path.exists(file):
        raw_file = io.open(file, mode='rb')

        detector = UniversalDetector()
        for line in raw_file.readlines():
            detector.feed(line)
            if detector.done: break
        detector.close()

        raw_file.close()

        encoding = detector.result["encoding"]

    decoding_fh = io.open(file, mode=mode, buffering=buffering,
                          encoding=encoding,
                          errors=errors,
                          newline=newline,
                          closefd=closefd)

    return decoding_fh
