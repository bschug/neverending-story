import argparse

def iter_two_lines(fp):
    lastline = fp.readline()
    for line in fp:
        yield lastline, line
        lastline = line


def is_wrapped_line(line, nextline, width):
    # If the next line is empty, this is definitely the end of a paragraph
    nextwords = nextline.split()
    if len(nextwords) == 0:
        return False

    # If the next word would push the line width above the limit, asssume
    # it's wrapped.
    if len(line) + 1 + len(nextwords[0]) > width:
        return True

    # Sometimes wrapping is based on printed width in a certain font instead
    # of by characters, so the line may be wrapped earlier. That's why we add
    # some wiggle room and consider all lines wrapped that don't end with a
    # punctuation (paragraphs usually do)
    if len(line) + 1 + len(nextwords[0]) > width * 0.66:
        return line.strip()[-1] not in ".:!'\"”"

    # Shorter lines are newlines on purpose
    return True


def remove_non_paragraph_newlines(fpin, fpout, width=80):
    for line, nextline in iter_two_lines(fpin):
        if is_wrapped_line(line, nextline, width):
            fpout.write(line[:-1])
            fpout.write(' ')
        else:
            fpout.write(line)
    fpout.write(nextline)


def main(args):
    with open(args.infile) as fpin:
        with open(args.outfile, 'w') as fpout:
            remove_non_paragraph_newlines(fpin, fpout, args.width)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('infile')
    ap.add_argument('outfile')
    ap.add_argument('--width', default=80, type=int)
    return ap.parse_args()


if __name__ == '__main__':
    main(parse_args())