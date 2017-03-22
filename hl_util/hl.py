#!/usr/bin/python -u

import argparse
import sys

parser = argparse.ArgumentParser(description='Filter logcat by package name')
parser.add_argument('file', nargs='*', help='File path', default=None)
parser.add_argument('--grep', dest='grep_words', type=str, default='', help='Filter lines with words in log messages. The words are delimited with \'\\|\', where each word can be tailed with a color initialed with \'\\\\\'. If no color is specified, \'RED\' will be the default color. For example, option --grep=\"word1\\|word2\\\\CYAN\" means to filter out all lines containing either word1 or word2, and word1 will appear in default color RED while word2 will be in CYAN. Supported colors (case ignored): {BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BG_BLACK, BG_RED, BG_GREEN, BG_YELLOW, BG_BLUE, BG_MAGENTA, BG_CYAN, BG_WHITE}. The color with prefix \'BG_\' is background color')
parser.add_argument('--hl', dest='highlight_words', type=str, default='', help='Words to highlight in log messages. Unlike --grep option, this option will only highlight the specified words with specified color but does not filter any lines. Except this, the format and supported colors are the same as --grep')
parser.add_argument('--grepv', dest='grepv_words', type=str, default='', help='Exclude lines with words from log messages. The format and supported colors are the same as --grep. Note that if both --grepv and --grep are provided and they contain the same word, the line will always show, which means --grep overwrites --grepv for the same word they both contain')
parser.add_argument('--igrep', dest='igrep_words', type=str, default='', help='The same as --grep, just ignore case')
parser.add_argument('--ihl', dest='ihighlight_words', type=str, default='', help='The same as --hl, just ignore case')
parser.add_argument('--igrepv', dest='igrepv_words', type=str, default='', help='The same as --grepv, just ignore case')

args = parser.parse_args()

file_path = args.file

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

color_dict = {'BLACK': BLACK, 'RED': RED, 'GREEN': GREEN, 'YELLOW': YELLOW, 'BLUE': BLUE, 'MAGENTA': MAGENTA, 'CYAN': CYAN, 'WHITE': WHITE}
contrast_color_dict = {BLACK: WHITE, RED: BLACK, GREEN: BLACK, YELLOW: BLACK, BLUE: WHITE, MAGENTA: BLACK, CYAN: BLACK, WHITE: BLACK}


def extract_color_from_word(word):
    w = word
    c = RED
    bg = False
    delimiter = '\\'
    index = word.rfind(delimiter)
    if index is not -1:
        w = word[0:index]
        try:
            color_word = word[index + len(delimiter):].upper()
            if color_word[:3] == 'BG_':
                bg = True
                color_word = color_word[3:]
            c = color_dict[color_word]
        except KeyError:
            c = RED
    return w, c, bg


def parse_words_with_color(words):
    words_with_color = []
    for word in words:
        words_with_color.append(extract_color_from_word(word))
    return words_with_color


def empty(vector):
    return vector is None or len(vector) <= 0


grep_words_with_color = None
highlight_words_with_color = None
excluded_words = None
igrep_words_with_color = None
ihighlight_words_with_color = None
iexcluded_words = None

if not empty(args.grep_words):
    grep_words_with_color = parse_words_with_color(args.grep_words.split('\|'))
if not empty(args.highlight_words):
    highlight_words_with_color = parse_words_with_color(args.highlight_words.split('\|'))
if not empty(args.grepv_words):
    excluded_words = args.grepv_words.split('\|')

if not empty(args.igrep_words):
    igrep_words_with_color = parse_words_with_color(args.igrep_words.split('\|'))
if not empty(args.ihighlight_words):
    ihighlight_words_with_color = parse_words_with_color(args.ihighlight_words.split('\|'))
if not empty(args.igrepv_words):
    iexcluded_words = args.igrepv_words.split('\|')

RESET = '\033[0m'
EOL = '\033[K'


def termcolor(fg=None, bg=None, ul=False):
    codes = []
    if fg is not None:
        codes.append('3%d' % fg)
    if bg is not None:
        codes.append('10%d' % bg)
    return '\033[%s%sm' % ('4;' if ul else '', ';'.join(codes) if codes else '')


def colorize(message, fg=None, bg=None, ul=False):
    return termcolor(fg, bg, ul) + message + RESET


def does_match_grep(message, grep_words_with_color, ignore_case):
    if not empty(grep_words_with_color):
        for word, color, bg in grep_words_with_color:
            if len(word) > 0 and ((not ignore_case and word in message) or (ignore_case and word.upper() in message.upper())):
                return True
    return False


def does_match_grepv(message, grepv_words, ignore_case):
    if not empty(grepv_words):
        for word in grepv_words:
            if len(word) > 0 and ((not ignore_case and word in message) or (ignore_case and word.upper() in message.upper())):
                return True
    return False


def colorize_substr(str, start_index, end_index, color, bg):
    fg_color = None
    bg_color = None
    ul = False
    if bg:
        bg_color = color
        try:
            fg_color = contrast_color_dict[color]
        except KeyError:
            pass
    else:
        fg_color = color
        ul = True
    colored_word = colorize(str[start_index:end_index], fg_color, bg_color, ul=ul)
    return str[:start_index] + colored_word + str[end_index:], start_index + len(colored_word)


def highlight(line, words_to_color, ignore_case=False, prev_line=None, next_line=None):
    for word, color, bg in words_to_color:
        if len(word) > 0:
            index = 0
            while True:
                try:
                    if ignore_case:
                        index = line.upper().index(word.upper(), index)
                    else:
                        index = line.index(word, index)
                except ValueError:
                    break
                line, index = colorize_substr(line, index, index + len(word), color, bg)

            if not empty(prev_line):
                for i in range(1, len(word)):
                    wrapped_word = prev_line[-i:] + line[:len(word) - i]
                    if (not ignore_case and word == wrapped_word) or (ignore_case and word.upper() == wrapped_word.upper()):
                        line, index = colorize_substr(line, 0, len(word) - i, color, bg)
                        break

            if not empty(next_line):
                for i in range(1, len(word)):
                    wrapped_word = line[-i:] + next_line[:len(word) - i]
                    if (not ignore_case and word == wrapped_word) or (ignore_case and word.upper() == wrapped_word.upper()):
                        line, index = colorize_substr(line, len(line) - i, len(line), color, bg)
                        break

    return line

print(file_path[0])
f = None
if empty(file_path) or empty(file_path[0]):
    input_src = sys.stdin
else:
    try:
        f = open(file_path[0], 'r')
        input_src = f
    except (OSError, IOError) as e:
        print('Can\'t open file \'' + file_path + '\'')
        sys.exit(-1)

while True:
    try:
        line = input_src.readline().decode('utf-8')
        if not line:
            break
    except KeyboardInterrupt:
        break

    matches_grep = does_match_grep(line, grep_words_with_color, False)
    matches_igrep = does_match_grep(line, igrep_words_with_color, True)

    matches_grepv = does_match_grepv(line, excluded_words, False)
    matches_igrepv = does_match_grepv(line, iexcluded_words, True)

    if matches_grep or matches_igrep:
        pass
    elif matches_grepv or matches_igrepv:
        continue
    else:
        if empty(grep_words_with_color) and empty(igrep_words_with_color):
            pass
        else:
            continue

    words_to_color = []
    if grep_words_with_color is not None:
        words_to_color += grep_words_with_color
    if highlight_words_with_color is not None:
        words_to_color += highlight_words_with_color

    iwords_to_color = []
    if igrep_words_with_color is not None:
        iwords_to_color += igrep_words_with_color
    if ihighlight_words_with_color is not None:
        iwords_to_color += ihighlight_words_with_color

    line = highlight(line, words_to_color, ignore_case=False)
    line = highlight(line, iwords_to_color, ignore_case=True)

    print(line.encode('utf-8'))

if f is not None:
    f.close()
