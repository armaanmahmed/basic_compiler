from sys import argv

# macros for the preprocessor
DEFINE_TEXT = "#define "
SINGLE_LINE_COMMENT_TEXT = "//"
MULTI_LINE_COMMENT_BEGIN = "/*"
MULTI_LINE_COMMENT_END = "*/"

# some exception classes for organization


class CommentParseException(Exception):
    pass


def _remove_comments(text: str) -> str:
    lines_without_multiline_comments: list[str] = []
    in_multiline_comment = False

    # strip out multiline comments
    for line in text.splitlines():
        # handles the case of multiple multiline comments in a single line
        line_frags = []
        left_to_parse = line

        # iterate through and case on whether in multiline comment
        # and the presence of the next comment start/end symbol
        while left_to_parse:
            if not in_multiline_comment:
                cut_start_idx = left_to_parse.find(MULTI_LINE_COMMENT_BEGIN)

                # if no multiline comment marker found, simply append and advance
                if cut_start_idx == -1:
                    line_frags.append(left_to_parse)
                    break
                else:
                    # if found, append everything until then and cut the marker too
                    in_multiline_comment = True
                    line_frags.append(left_to_parse[:cut_start_idx])
                    left_to_parse = left_to_parse[cut_start_idx +
                                                  len(MULTI_LINE_COMMENT_BEGIN):]
            else:
                cut_end_idx = left_to_parse.find(MULTI_LINE_COMMENT_END)
                # if not found, then everything else is comment so can be discarded
                if cut_end_idx == -1:
                    break
                else:
                    left_to_parse = left_to_parse[cut_end_idx +
                                                  len(MULTI_LINE_COMMENT_END):]
                    in_multiline_comment = False

        lines_without_multiline_comments.append("".join(line_frags))

    if in_multiline_comment:
        raise CommentParseException("Unpaired multiline comment syntax")

    lines_without_comments: list[str] = []

    # strip out single line comments
    for line in lines_without_multiline_comments:
        comment_idx = line.find(SINGLE_LINE_COMMENT_TEXT)
        if comment_idx == -1:
            lines_without_comments.append(line)
        else:
            lines_without_comments.append(line[:comment_idx])

    text_without_comments = "\n".join(
        (l for l in lines_without_comments if l.strip()))

    return text_without_comments


def _extract_mappings(raw_text_str: str) -> tuple[list[str], dict[str, str]]:
    mappings = {}
    text_lines = []

    for line in raw_text_str.splitlines():
        if line.startswith(DEFINE_TEXT):
            # convert from '#define  key value' -> 'key value'
            stripline = line.removeprefix(DEFINE_TEXT).strip()
            sep_idx = stripline.find(" ")

            # mappings[key] = value
            if sep_idx != -1:
                mappings[stripline[:sep_idx]] = stripline[sep_idx:].strip()
        else:
            text_lines.append(line)

    return mappings, text_lines


def _process_macros(raw_text_lines: list[str], macro_map: dict[str, str]):
    processed_lines = []

    for line in raw_text_lines:
        # prevent infinite substitutions - may update based on actual preprocessor behavior
        loop_check = set()
        processed_line = line

        # while this line contains any macros not in the already-replaced set
        while any(processed_line.find(key) != -1 for key in macro_map if key not in loop_check):
            for key, value in macro_map.items():
                if processed_line.find(key) != -1:
                    processed_line = processed_line.replace(key, value)
                    loop_check.add(key)

        # once fully processed, add the line to the list
        processed_lines.append(processed_line)

    return processed_lines


def preprocess(raw_text: str, debug=False):
    # pass one: extract macro mappings
    mappings, lines_without_defines = _extract_mappings(raw_text)

    if debug:
        print(f'mappings: {mappings}')
        print(f'lines without defines: {lines_without_defines}')

    # pass two: process macros
    substituted_text_lines = _process_macros(lines_without_defines, mappings)
    processed_text = "\n".join(substituted_text_lines)

    # pass three: remove comments
    full_text = _remove_comments(processed_text)

    return full_text


if __name__ == "__main__":
    if len(argv) < 2:
        filename = input("Enter a file: ")
    else:
        filename = argv[1]

    with open(filename, 'r') as file:
        preprocessed_text = preprocess(file.read())
        print(preprocessed_text)
